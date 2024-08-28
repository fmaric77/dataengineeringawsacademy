import os
import json
import boto3
import numpy as np
import pandas as pd
import requests
from opensearchpy import OpenSearch

# Load dataset
dataset_path = "cryptonews.csv"
df = pd.read_csv(dataset_path)

# Step 2: Extract and Combine Text
df = df.head(100)
df['content'] = df['title'] + " " + df['text']

# Step 3: Extract Sentiment from CSV
def extract_sentiment(sentiment_str):
    sentiment_dict = json.loads(sentiment_str.replace("'", "\""))
    return sentiment_dict['class']

df['sentiment'] = df['sentiment'].apply(extract_sentiment)

# Step 4: Embed Text Using Amazon Titan
client = boto3.client('bedrock-runtime')
model_id = "amazon.titan-embed-text-v1"
accept = "application/json"
content_type = "application/json"
expected_dimension = 1536

def embed_text(text):
    body = json.dumps({"inputText": text})
    response = client.invoke_model(
        body=body,
        modelId=model_id,
        accept=accept,
        contentType=content_type
    )
    response_body = json.loads(response.get('body').read())
    embedding = np.array(response_body['embedding'])
    if embedding.shape[0] != expected_dimension:
        print(f"Invalid embedding dimension: {embedding.shape[0]} for text: {text}")
        return None
    return embedding

df['embedding'] = df['content'].apply(embed_text)

# Step 5: Store Vectors in OpenSearch
opensearch_url = "https://search-academy-02-sjb2kmrb4hzureuudlz6y5ukr4.eu-central-1.es.amazonaws.com"
username = "academy-opensearch"
password = "8q%a^6uP@Yoqg71LIJEQVVhAu3lcYSOx#@Qs#w7E2IRJ3^!uIp"

opensearch = OpenSearch(
    hosts=[opensearch_url],
    http_auth=(username, password)
)

# Delete the existing index if it exists
index_name = "cryptonews"
if opensearch.indices.exists(index=index_name):
    opensearch.indices.delete(index=index_name)

# Create a new index with the correct mapping
index_body = {
    "settings": {
        "index": {
            "knn": True
        }
    },
    "mappings": {
        "properties": {
            "content": {"type": "text"},
            "embedding": {"type": "knn_vector", "dimension": expected_dimension},
            "sentiment": {"type": "keyword"},
            "source": {"type": "keyword"},
            "subject": {"type": "keyword"},
            "url": {"type": "keyword"},
            "title": {"type": "text"},
            "text": {"type": "text"}  # Ensure text is indexed
        }
    }
}

opensearch.indices.create(index=index_name, body=index_body)

# Index the documents
for _, row in df.iterrows():
    if row['embedding'] is not None and len(row['embedding']) == expected_dimension:
        document = {
            "content": row['content'],
            "embedding": row['embedding'].tolist(),
            "sentiment": row['sentiment'],
            "source": row['source'],
            "subject": row['subject'],
            "url": row['url'],
            "title": row['title'],  # Include title in the document
            "text": row['text']  # Include text in the document
        }
        opensearch.index(index=index_name, body=document)
        print(f"Indexed document: {row['content']}")
    else:
        print(f"Skipping document with null or invalid embedding: {row['content']}")

# Step 6: Query Vector Store
query_text = "What are the latest news on bitcoin prices?"
query_embedding = embed_text(query_text)

if query_embedding is not None and query_embedding.shape[0] == expected_dimension:
    print(f"Query embedding dimension: {query_embedding.shape[0]}")
    results = opensearch.search(
        index=index_name,
        body={
            "query": {
                "bool": {
                    "must": {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding.tolist(),
                                "k": 5
                            }
                        }
                    },
                    "filter": {
                        "term": {"sentiment": "positive"}
                    }
                }
            }
        }
    )

    if results['hits']['hits']:
        for result in results['hits']['hits']:
            source = result['_source']
            print(f"Title: {source['title']}")
            print(f"Text: {source['text']}")
            print(f"URL: {source['url']}")
            print(f"Sentiment: {source['sentiment']}")
            print(f"Source: {source['source']}")
            print(f"Subject: {source['subject']}")
            print("\n")
    else:
        print("No results found.")
else:
    print(f"Query embedding has invalid dimension: {query_embedding.shape[0]}")