#2nd day of day2 in its own file
import os
import random
import json
import boto3
import numpy as np
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
from html import unescape
import chromadb
from chromadb.utils import embedding_functions
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to sanitize input text
def sanitize_text(text):
    text = re.sub(r'<.*?>', '', text)
    text = unescape(text)
    text = re.sub(r'[^\w\s]', '', text)
    text = ''.join(c for c in text if c.isprintable())
    text = text.encode('utf-8', 'ignore').decode('utf-8')
    text = text[:1000]
    return text

# Load IMDB dataset and select 200 random reviews
def load_imdb_reviews(directory, num_samples=200):
    reviews = []

    def load_review(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for label in ["pos", "neg"]:
            path = os.path.join(directory, label)
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path) and file.endswith('.txt'):
                    futures.append(executor.submit(load_review, file_path))
        
        for future in futures:
            reviews.append(future.result())
    
    selected_reviews = random.sample(reviews, num_samples)
    return selected_reviews

# Initialize the Amazon Titan Embeddings G1 - Text model using boto3
def embed_reviews_with_titan(reviews):
    client = boto3.client('bedrock-runtime')
    model_id = "amazon.titan-embed-text-v1"
    accept = "application/json"
    content_type = "application/json"
    embeddings = []
    
    def embed_review(review):
        try:
            sanitized_review = sanitize_text(review)
            body = json.dumps({"inputText": sanitized_review})
            response = client.invoke_model(
                body=body,
                modelId=model_id,
                accept=accept,
                contentType=content_type
            )
            response_body = json.loads(response.get('body').read())
            return np.array(response_body['embedding'])
        except client.exceptions.ValidationException as e:
            return None
        except Exception as e:
            return None
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(embed_review, review) for review in reviews]
        for future in futures:
            result = future.result()
            if result is not None:
                embeddings.append(result)
    
    return np.array(embeddings)

# Main function
def main():
    imdb_directory = "C:/Users/Academy2024/Desktop/fmaric/PROMPTENGINEERING/aclImdb/test"
    query = "action movie"
    
    reviews = load_imdb_reviews(imdb_directory)
    
    # Embed reviews using Amazon Titan Embeddings G1 - Text
    titan_embeddings = embed_reviews_with_titan(reviews)
    if len(titan_embeddings) == 0:
        raise ValueError("No embeddings generated")
    
    # Initialize ChromaDB vector store
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection("imdb_reviews")
    
    # Populate ChromaDB vector store
    for review, embedding in zip(reviews, titan_embeddings):
        label = "positive" if "pos" in review else "negative"
        unique_id = str(uuid.uuid4())
        collection.add(ids=[unique_id], embeddings=[embedding.tolist()], metadatas=[{"label": label, "text": review}])
    
    # Embed the query text
    query_embedding = embed_reviews_with_titan([query])[0].tolist()
    
    # Find 5 most similar reviews in the "positive" category
    positive_results = collection.query(query_embeddings=[query_embedding], n_results=5, where={"label": "positive"})
    if 'metadatas' in positive_results:
        logging.info("\nTop 5 similar reviews in 'positive' category:")
        for i, metadata in enumerate(positive_results['metadatas'][0], 1):
            logging.info(f"\nReview {i}:")
            logging.info(f"Text: {metadata['text']}")
            logging.info(f"Label: {metadata['label']}")
    
    # Find 5 most similar reviews in the "negative" category
    negative_results = collection.query(query_embeddings=[query_embedding], n_results=5, where={"label": "negative"})
    if 'metadatas' in negative_results:
        logging.info("\nTop 5 similar reviews in 'negative' category:")
        for i, metadata in enumerate(negative_results['metadatas'][0], 1):
            logging.info(f"\nReview {i}:")
            logging.info(f"Text: {metadata['text']}")
            logging.info(f"Label: {metadata['label']}")
    
if __name__ == "__main__":
    main()