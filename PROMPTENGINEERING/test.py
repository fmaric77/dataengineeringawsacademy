# Cell 1: Import necessary libraries and set up logging
import pandas as pd
import ast
import random
import logging
from langchain import PromptTemplate
from langchain_aws import ChatBedrock
from langchain_core.output_parsers import StrOutputParser
from sklearn.metrics import accuracy_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cell 2: Load the dataset and define a function to parse the sentiment column
dataset_path = "cryptonews.csv"
logging.info(f"Loading dataset from {dataset_path}")
df = pd.read_csv(dataset_path, names=["timestamp", "sentiment", "source", "category", "text", "title", "url"])

def parse_sentiment(sentiment_str):
    try:
        return ast.literal_eval(sentiment_str)['class']
    except (ValueError, SyntaxError, KeyError):
        return None

logging.info("Parsing sentiment column")
df['sentiment'] = df['sentiment'].apply(parse_sentiment)
df = df.dropna(subset=['sentiment'])

# Cell 3: Combine title and text, drop unnecessary columns, and select samples
logging.info("Combining title and text columns into content")
df['content'] = df['title'] + " " + df['text']
df = df.drop(columns=['timestamp', 'source', 'category', 'url'])

logging.info("Selecting 2500 random positive and negative samples")
positive_samples = df[df['sentiment'] == 'positive'].sample(n=2500, random_state=42)
negative_samples = df[df['sentiment'] == 'negative'].sample(n=2500, random_state=42)

logging.info("Combining and shuffling the dataset")
combined_df = pd.concat([positive_samples, negative_samples]).sample(frac=1).reset_index(drop=True)
texts = combined_df['content'].tolist()
sentiments = combined_df['sentiment'].tolist()
texts = [str(text) for text in texts]

# Cell 4: Set up sentiment classification chain using LangChain with Bedrock model
logging.info("Setting up sentiment classification chain using LangChain with Bedrock model")
model_id = "anthropic.claude-3-haiku-20240307-v1:0"
llm = ChatBedrock(model_id=model_id)

# Updated sentiment template with examples
sentiment_template = PromptTemplate(
    template="""Classify the sentiment of this text: {text}
Examples:
Positive: "I love this product! It works great and exceeds my expectations."
Negative: "This is the worst experience I've ever had. Completely dissatisfied."
""",
    input_variables=["text"]
)

parser = StrOutputParser()
sentiment_chain = sentiment_template | llm | parser

def classify_sentiment(text):
    result = sentiment_chain.invoke({"text": text})
    return "positive" if "positive" in result.lower() else "negative"

# Cell 5: Classify samples and calculate accuracy
logging.info("Classifying 20 examples from each sentiment class and calculating accuracy")
sample_texts = positive_samples['content'].tolist()[:20] + negative_samples['content'].tolist()[:20]
sample_sentiments = ['positive'] * 20 + ['negative'] * 20

predicted_sentiments = [classify_sentiment(text) for text in sample_texts]

accuracy = accuracy_score(sample_sentiments, predicted_sentiments)
logging.info(f"Accuracy: {accuracy * 100:.2f}%")

# Cell 6: Define reverse sentiment chain and functions for adjective extraction and haiku generation
reverse_template = PromptTemplate(template="Reverse the sentiment of this text: {text}", input_variables=["text"])
reverse_chain = reverse_template | llm | parser

def reverse_sentiment(text):
    return reverse_chain.invoke({"text": text})

logging.info("Setting up adjective extraction chain using LangChain with Bedrock model")
adjective_template = PromptTemplate(template="Extract adjectives from this text: {text}", input_variables=["text"])
adjective_chain = adjective_template | llm | parser

def extract_adjectives(text):
    result = adjective_chain.invoke({"text": text})
    # Extract the adjectives from the response
    adjectives = result.split("\n")[1:]  # Skip the first line which is the header
    adjectives = [adj.split(". ")[1] for adj in adjectives if ". " in adj]  # Extract the adjective part
    logging.info(f"Extracted adjectives: {adjectives}")
    return adjectives

def generate_haiku(adjectives, theme):
    if len(adjectives) < 3:
        logging.warning("Not enough adjectives to generate a haiku.")
        return "Not enough adjectives to generate a haiku."
    haiku = f"{theme} are {adjectives[0]},\n{adjectives[1]} and {adjectives[2]},\n{theme} in the sky."
    return haiku

def process_review(review, theme):
    logging.info(f"Processing review for theme: {theme}")
    reversed_text = reverse_sentiment(review)
    adjectives = extract_adjectives(reversed_text)
    haiku = generate_haiku(adjectives, theme)
    return haiku

# Cell 7: Example usage
review = "I watch this amazing movie every single night, the green actor is dreamy and I am in love with the great story."
logging.info("Original Review: " + review)
logging.info("Reversed Sentiment Review: " + reverse_sentiment(review))
logging.info("Extracted Adjectives: " + str(extract_adjectives(reverse_sentiment(review))))
logging.info("Haiku about birds: " + process_review(review, "birds"))
logging.info("Haiku about octopuses: " + process_review(review, "octopuses"))