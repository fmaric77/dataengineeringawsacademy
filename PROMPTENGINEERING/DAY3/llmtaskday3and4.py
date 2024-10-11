import os
import shutil
import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import BertTokenizer, BertForMaskedLM, DataCollatorForLanguageModeling, Trainer, TrainingArguments, GPT2Tokenizer, GPT2LMHeadModel, pipeline
from datasets import Dataset, DatasetDict
import warnings
import ast
import logging
import torch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress the FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")

# Load the dataset
dataset_path = "cryptonews.csv"
logging.info(f"Loading dataset from {dataset_path}")
df = pd.read_csv(dataset_path, names=["timestamp", "sentiment", "source", "category", "text", "title", "url"])

# Function to safely parse the sentiment column
def parse_sentiment(sentiment_str):
    try:
        return ast.literal_eval(sentiment_str)['class']
    except (ValueError, SyntaxError, KeyError):
        return None

# Parse the sentiment column to extract the sentiment class
logging.info("Parsing sentiment column")
df['sentiment'] = df['sentiment'].apply(parse_sentiment)

# Drop rows with invalid sentiment values
logging.info("Dropping rows with invalid sentiment values")
df = df.dropna(subset=['sentiment'])

# Combine title and text
logging.info("Combining title and text columns into content")
df['content'] = df['title'] + " " + df['text']

# Drop unnecessary columns
df = df.drop(columns=['timestamp', 'source', 'category', 'url'])

# Select 2500 random examples from each category
logging.info("Selecting 2500 random positive and negative samples")
positive_samples = df[df['sentiment'] == 'positive'].sample(n=2500, random_state=42)
negative_samples = df[df['sentiment'] == 'negative'].sample(n=2500, random_state=42)

# Combine and shuffle the dataset
logging.info("Combining and shuffling the dataset")
combined_df = pd.concat([positive_samples, negative_samples]).sample(frac=1).reset_index(drop=True)

# Extract the textual content
logging.info("Extracting textual content")
texts = combined_df['content'].tolist()

# Ensure texts is a list of strings
texts = [str(text) for text in texts]

# Check if texts list is not empty
if not texts:
    logging.error("The texts list is empty. Please check the dataset and ensure it contains data.")
    raise ValueError("The texts list is empty. Please check the dataset and ensure it contains data.")

# Tokenize the dataset for MLM
logging.info("Tokenizing the dataset for MLM")
mlm_tokenizer = BertTokenizer.from_pretrained('prajjwal1/bert-tiny')
mlm_tokenized_texts = mlm_tokenizer(texts, truncation=True, padding=True, max_length=128, return_tensors='pt')

# Create a Hugging Face Dataset for MLM
logging.info("Creating Hugging Face Dataset for MLM")
mlm_dataset = Dataset.from_dict({
    'input_ids': mlm_tokenized_texts['input_ids'],
    'attention_mask': mlm_tokenized_texts['attention_mask']
})

# Data collator for MLM
logging.info("Creating data collator for MLM")
mlm_data_collator = DataCollatorForLanguageModeling(tokenizer=mlm_tokenizer, mlm=True, mlm_probability=0.15)

# Define the MLM model
logging.info("Defining the MLM model")
mlm_model = BertForMaskedLM.from_pretrained('prajjwal1/bert-tiny')

# Training arguments for MLM
logging.info("Setting training arguments for MLM")
mlm_training_args = TrainingArguments(
    output_dir='./mlm_results',
    overwrite_output_dir=True,
    num_train_epochs=3,
    per_device_train_batch_size=16,  
    save_steps=10_000,
    save_total_limit=2,
    fp16=False,  
    gradient_accumulation_steps=2,  
)

# Helper function to make tensors contiguous
def make_contiguous(model):
    for param in model.parameters():
        param.data = param.data.contiguous()

# Custom Trainer class to make tensors contiguous before saving
class CustomTrainer(Trainer):
    def _save_checkpoint(self, model, trial, metrics=None):
        make_contiguous(model)
        super()._save_checkpoint(model, trial, metrics)

# Check if MLM model already exists and is valid
if not os.path.exists('./mlm_results') or not os.path.exists('./mlm_results/config.json'):
    if os.path.exists('./mlm_results'):
        logging.warning("MLM model directory exists but is invalid. Deleting and retraining.")
        shutil.rmtree('./mlm_results')  # Delete the invalid directory
    logging.info("Training the MLM model")
    mlm_trainer = CustomTrainer(
        model=mlm_model,
        args=mlm_training_args,
        data_collator=mlm_data_collator,
        train_dataset=mlm_dataset,
    )
    mlm_trainer.train()
    logging.info("Saving the trained MLM model")
    mlm_trainer.save_model('./mlm_results')  
else:
    logging.info("MLM model already exists. Loading the trained model.")
    mlm_model = BertForMaskedLM.from_pretrained('./mlm_results')
    mlm_tokenizer = BertTokenizer.from_pretrained('prajjwal1/bert-tiny')

# Tokenize the dataset for CLM
logging.info("Tokenizing the dataset for CLM")
clm_tokenizer = GPT2Tokenizer.from_pretrained('sshleifer/tiny-gpt2')

# Add a padding token to the GPT-2 tokenizer
clm_tokenizer.add_special_tokens({'pad_token': '[PAD]'})

# Tokenize the texts with padding
clm_tokenized_texts = clm_tokenizer(texts, truncation=True, padding=True, max_length=128, return_tensors='pt')

# Create a Hugging Face Dataset for CLM
logging.info("Creating Hugging Face Dataset for CLM")
clm_dataset = Dataset.from_dict({
    'input_ids': clm_tokenized_texts['input_ids'],
    'attention_mask': clm_tokenized_texts['attention_mask']
})

# Data collator for CLM
logging.info("Creating data collator for CLM")
clm_data_collator = DataCollatorForLanguageModeling(tokenizer=clm_tokenizer, mlm=False)

# Define the CLM model
logging.info("Defining the CLM model")
clm_model = GPT2LMHeadModel.from_pretrained('sshleifer/tiny-gpt2')

# Resize the model embeddings to match the tokenizer
clm_model.resize_token_embeddings(len(clm_tokenizer))

# Training arguments for CLM
logging.info("Setting training arguments for CLM")
clm_training_args = TrainingArguments(
    output_dir='./clm_results',
    overwrite_output_dir=True,
    num_train_epochs=3,
    per_device_train_batch_size=16,  
    save_steps=10_000,
    save_total_limit=2,
    fp16=False,  
    gradient_accumulation_steps=2,  
)

# Check if CLM model already exists and is valid
if not os.path.exists('./clm_results') or not os.path.exists('./clm_results/config.json'):
    if os.path.exists('./clm_results'):
        logging.warning("CLM model directory exists but is invalid. Deleting and retraining.")
        shutil.rmtree('./clm_results')  # Delete the invalid directory
    logging.info("Training the CLM model")
    clm_trainer = CustomTrainer(
        model=clm_model,
        args=clm_training_args,
        data_collator=clm_data_collator,
        train_dataset=clm_dataset,
    )
    clm_trainer.train()
    logging.info("Saving the trained CLM model")
    clm_trainer.save_model('./clm_results')  # Save the model after training
else:
    logging.info("CLM model already exists. Loading the trained model.")
    clm_model = GPT2LMHeadModel.from_pretrained('./clm_results')
    clm_tokenizer = GPT2Tokenizer.from_pretrained('sshleifer/tiny-gpt2')
    clm_tokenizer.add_special_tokens({'pad_token': '[PAD]'})  # Ensure padding token is added
    clm_model.resize_token_embeddings(len(clm_tokenizer))  # Resize embeddings

# Ensure MLM model tensors are contiguous
make_contiguous(mlm_model)

# Ensure CLM model tensors are contiguous
make_contiguous(clm_model)

# Create pipelines
logging.info("Creating pipelines for text generation")
mlm_generator = pipeline('text-generation', model=mlm_model, tokenizer=mlm_tokenizer)
clm_generator = pipeline('text-generation', model=clm_model, tokenizer=clm_tokenizer)

# Generate text
logging.info("Generating text with MLM model")
mlm_output = mlm_generator("The best crypto is:", max_length=50)
logging.info("Generating text with CLM model")
clm_output = clm_generator("The best crypto is:", max_length=50)

logging.info(f"MLM Output: {mlm_output}")
logging.info(f"CLM Output: {clm_output}")

print("MLM Output:", mlm_output)
print("CLM Output:", clm_output)