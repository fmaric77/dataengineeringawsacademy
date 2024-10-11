import os
import json
import requests
import boto3
import numpy as np
from opensearchpy import OpenSearch
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory



# Global API key
API_KEY = "113c5d6f3c5b5365e1ae5e63039150abe56f0ec4cde2002798000cdcc0d67c23"

# OpenSearch configuration
opensearch_url = "https://search-academy-02-sjb2kmrb4hzureuudlz6y5ukr4.eu-central-1.es.amazonaws.com"
username = "academy-opensearch"
password = "8q%a^6uP@Yoqg71LIJEQVVhAu3lcYSOx#@Qs#w7E2IRJ3^!uIp"
index_name = "cryptonews"

opensearch = OpenSearch(
    hosts=[opensearch_url],
    http_auth=(username, password)
)

# Amazon Bedrock configuration
client = boto3.client('bedrock-runtime')
model_id = "amazon.titan-embed-text-v1"
accept = "application/json"
content_type = "application/json"
expected_dimension = 1536

# Define embed_text function using Amazon Titan
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

# Define retriever function
def retrieve_news(query_text):
    query_embedding = embed_text(query_text)
    if query_embedding is not None and query_embedding.shape[0] == expected_dimension:
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
                        }
                    }
                }
            }
        )
        return results['hits']['hits']
    return []

# Define tools
@tool
def fetch_current_price(crypto_symbol: str) -> str:
    """Fetch the current price of a cryptocurrency."""
    url = f"https://min-api.cryptocompare.com/data/price?fsym={crypto_symbol}&tsyms=USD"
    response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
    data = response.json()
    return f"The current price of {crypto_symbol} is ${data['USD']}."

@tool
def convert_price(from_symbol: str, to_symbol: str) -> str:
    """Convert the price of one cryptocurrency to another."""
    url = f"https://min-api.cryptocompare.com/data/price?fsym={from_symbol}&tsyms={to_symbol}"
    response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
    data = response.json()
    return f"The price of 1 {from_symbol} in {to_symbol} is {data[to_symbol]} {to_symbol}."

@tool
def fetch_historical_prices(crypto_symbol: str) -> str:
    """Fetch historical prices of a cryptocurrency for the past week."""
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={crypto_symbol}&tsym=USD&limit=6"
    response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
    data = response.json()
    prices = [day['close'] for day in data['Data']['Data']]
    return f"Historical prices for {crypto_symbol} in the past week: {prices}"

@tool
def fetch_crypto_news(crypto_symbol: str) -> str:
    """Fetch the latest news about a cryptocurrency."""
    news_hits = retrieve_news(crypto_symbol)
    if news_hits:
        seen_titles = set()
        news_summary = f"According to the latest news about {crypto_symbol}:\n"
        for hit in news_hits:
            title = hit['_source']['title']
            if title not in seen_titles:
                seen_titles.add(title)
                news_summary += f"- {title}: {hit['_source']['text']}\n"
        return news_summary
    return f"No recent news found for {crypto_symbol}."

# Bind tools to model
chat_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
chat_model = ChatBedrock(model_id=chat_model_id).bind_tools([fetch_current_price, convert_price, fetch_historical_prices, fetch_crypto_news])

# Create agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use the tools at your disposal to answer questions about cryptocurrencies."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])
memory = ChatMessageHistory()

tools = [fetch_current_price, convert_price, fetch_historical_prices, fetch_crypto_news]
agent = create_tool_calling_agent(chat_model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
with_message_history = RunnableWithMessageHistory(agent_executor, lambda x: memory, input_messages_key="input")

# Chatbot main loop
def handle_user_input(user_input):
    try:
        response = with_message_history.invoke({"input": user_input},config={"configurable": {"session_id": "stringx"}})
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")

print("Chatbot is running. Type 'END' to terminate.")
while True:
    user_input = input("User: ")
    if user_input == "END":
        print("Ending conversation. Goodbye!")
        break
    handle_user_input(user_input)