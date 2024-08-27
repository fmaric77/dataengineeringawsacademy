#%%
import random
import os
import boto3
import numpy as np
import logging
import json
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ThreadPoolExecutor
from html import unescape

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to sanitize input text
def sanitize_text(text):
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Unescape HTML entities
    text = unescape(text)
    # Remove or escape special characters
    text = re.sub(r'[^\w\s]', '', text)
    # Remove non-printable characters
    text = ''.join(c for c in text if c.isprintable())
    # Ensure proper encoding
    text = text.encode('utf-8', 'ignore').decode('utf-8')
    # Truncate text to a reasonable length if necessary
    text = text[:1000]  # Assuming the model expects a maximum of 1000 characters
    return text

# Load IMDB dataset and select 50 random reviews
def load_imdb_reviews(directory, num_samples=50):
    logging.info(f"Loading IMDB reviews from directory: {directory}")
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
    logging.info(f"Selected {num_samples} random reviews")
    return selected_reviews

# Initialize the all-MiniLM-L6-v2 model from sentence-transformers
def embed_reviews_with_minilm(reviews):
    logging.info("Embedding reviews using all-MiniLM-L6-v2 model")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(reviews, batch_size=32, show_progress_bar=True)
    logging.info("Completed embedding reviews with all-MiniLM-L6-v2")
    return embeddings

# Initialize the Amazon Titan Embeddings G1 - Text model using boto3
def embed_reviews_with_titan(reviews):
    logging.info("Embedding reviews using Amazon Titan Embeddings G1 - Text model")
    client = boto3.client('bedrock-runtime')
    model_id = "amazon.titan-embed-text-v1"
    accept = "application/json"
    content_type = "application/json"
    embeddings = []
    
    def embed_review(review):
        try:
            sanitized_review = sanitize_text(review)
            body = json.dumps({"inputText": sanitized_review})
            logging.debug(f"Request body: {body}")
            response = client.invoke_model(
                body=body,
                modelId=model_id,
                accept=accept,
                contentType=content_type
            )
            response_body = json.loads(response.get('body').read())
            logging.debug(f"Response body: {response_body}")
            return np.array(response_body['embedding'])
        except client.exceptions.ValidationException as e:
            logging.error(f"Validation error embedding review: {e}")
            logging.error(f"Detailed error message: {e.response['Error']['Message']}")
            logging.error(f"Request body: {body}")
            return None
        except Exception as e:
            logging.error(f"Error embedding review: {e}")
            return None
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(embed_review, review) for review in reviews]
        for future in futures:
            result = future.result()
            if result is not None:
                embeddings.append(result)
    
    logging.info("Completed embedding reviews with Amazon Titan Embeddings G1 - Text")
    return np.array(embeddings)

# Calculate cosine similarity
def calculate_cosine_similarity(embedding, embeddings):
    logging.info("Calculating cosine similarity")
    similarities = cosine_similarity([embedding], embeddings)[0]
    logging.info("Cosine similarity calculation completed")
    return similarities

# Find top 5 closest and top 5 most dissimilar reviews
def find_top_reviews(similarities, reviews, top_n=5):
    logging.info(f"Finding top {top_n} closest and most dissimilar reviews")
    sorted_indices = np.argsort(similarities)
    top_closest = sorted_indices[-top_n:][::-1]
    top_dissimilar = sorted_indices[:top_n]
    logging.info("Top reviews found")
    return ([reviews[i] for i in top_closest], [similarities[i] for i in top_closest]), ([reviews[i] for i in top_dissimilar], [similarities[i] for i in top_dissimilar])

# Main function
def main():
    imdb_directory = "C:/Users/Academy2024/Desktop/fmaric/PROMPTENGINEERING/aclImdb/test"
    query = "The main actor’s performance was incredible."
    
    logging.info("Starting main function")
    
    reviews = load_imdb_reviews(imdb_directory)
    
    # Embed reviews using all-MiniLM-L6-v2
    minilm_embeddings = embed_reviews_with_minilm(reviews)
    query_embedding_minilm = embed_reviews_with_minilm([query])[0]
    similarities_minilm = calculate_cosine_similarity(query_embedding_minilm, minilm_embeddings)
    (closest_minilm, closest_minilm_scores), (dissimilar_minilm, dissimilar_minilm_scores) = find_top_reviews(similarities_minilm, reviews)
    
    try:
        # Embed reviews using Amazon Titan Embeddings G1 - Text
        titan_embeddings = embed_reviews_with_titan(reviews)
        if len(titan_embeddings) == 0:
            logging.error("No embeddings were generated using Amazon Titan Embeddings G1 - Text")
            raise ValueError("No embeddings generated")
        
        query_embedding_titan = embed_reviews_with_titan([query])
        if len(query_embedding_titan) == 0:
            logging.error("No embedding was generated for the query using Amazon Titan Embeddings G1 - Text")
            raise ValueError("No query embedding generated")
        
        query_embedding_titan = query_embedding_titan[0]
        similarities_titan = calculate_cosine_similarity(query_embedding_titan, titan_embeddings)
        (closest_titan, closest_titan_scores), (dissimilar_titan, dissimilar_titan_scores) = find_top_reviews(similarities_titan, reviews)
        
        logging.info("Printing results for Amazon Titan Embeddings G1 - Text")
        
        print("\nTop 5 closest reviews using Amazon Titan Embeddings G1 - Text:")
        for review, score in zip(closest_titan, closest_titan_scores):
            print(f"{score:.4f} - {review}")
        
        print("\nTop 5 most dissimilar reviews using Amazon Titan Embeddings G1 - Text:")
        for review, score in zip(dissimilar_titan, dissimilar_titan_scores):
            print(f"{score:.4f} - {review}")
    
    except Exception as e:
        logging.error(f"Skipping Amazon Titan Embeddings G1 - Text due to error: {e}")
    
    logging.info("Printing results for all-MiniLM-L6-v2")
    
    print("Top 5 closest reviews using all-MiniLM-L6-v2:")
    for review, score in zip(closest_minilm, closest_minilm_scores):
        print(f"{score:.4f} - {review}")
    
    print("\nTop 5 most dissimilar reviews using all-MiniLM-L6-v2:")
    for review, score in zip(dissimilar_minilm, dissimilar_minilm_scores):
        print(f"{score:.4f} - {review}")
    
    logging.info("Main function completed")

if __name__ == "__main__":
    main()

#DAY2-2.PY contains the code for the second part od day 2