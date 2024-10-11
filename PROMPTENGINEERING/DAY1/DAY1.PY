#%%
import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from gensim.models import Word2Vec
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(message)s')

test_data = None

def preprocess_text(text):
    text = re.sub(r'[^\w\s]', '', text)  
    text = text.lower()  
    return text.split() 

def load_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return preprocess_text(content)
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return []

def load_data(directory, is_test_data=False):
    global test_data
    data = []
    with ThreadPoolExecutor() as executor:
        futures = []
        for label in ["pos", "neg"]:
            path = os.path.join(directory, label)
            if not os.path.exists(path) or not os.path.isdir(path):
                logging.error(f"Invalid directory: {path}")
                continue
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    futures.append(executor.submit(load_file, file_path))
        for future in as_completed(futures):
            data.append(future.result())
    if is_test_data:
        test_data = data
    return data

cbow_model_path = "cbow_model.model"
skipgram_model_path = "skipgram_model.model"

if os.path.exists(cbow_model_path) and os.path.exists(skipgram_model_path):
    logging.info("Loading existing CBOW and Skip-Gram models...")
    cbow_model = Word2Vec.load(cbow_model_path)
    skipgram_model = Word2Vec.load(skipgram_model_path)
else:
    logging.info("Loading training data...")
    train_data = load_data("C:/Users/Academy2024/Desktop/fmaric/PROMPTENGINEERING/aclImdb/train")
    logging.info(f"Loaded {len(train_data)} training samples.")
    print("First 5 training samples:", train_data[:5])

    if len(train_data) == 0:
        logging.error("Training data is empty. Exiting...")
        exit(1)

    logging.info("Training CBOW Word2Vec model...")
    cbow_model = Word2Vec(vector_size=100, window=5, min_count=1, sg=0)
    cbow_model.build_vocab(train_data)
    cbow_model.train(train_data, total_examples=cbow_model.corpus_count, epochs=cbow_model.epochs)
    cbow_model.save(cbow_model_path)

    logging.info("Training Skip-Gram Word2Vec model...")
    skipgram_model = Word2Vec(vector_size=100, window=5, min_count=1, sg=1)
    skipgram_model.build_vocab(train_data)
    skipgram_model.train(train_data, total_examples=skipgram_model.corpus_count, epochs=skipgram_model.epochs)
    skipgram_model.save(skipgram_model_path)

logging.info("Finding top 10 words similar to 'love' using CBOW model...")
similar_words_cbow = cbow_model.wv.most_similar("love", topn=10)
logging.info("Finding top 10 words similar to 'love' using Skip-Gram model...")
similar_words_skipgram = skipgram_model.wv.most_similar("love", topn=10)

print("CBOW Model - Top 10 words similar to 'love':", similar_words_cbow)
print("Skip-Gram Model - Top 10 words similar to 'love':", similar_words_skipgram)
#%%
def sentence_vector(sentence, model):
    words = preprocess_text(sentence)
    return np.mean([model.wv[word] for word in words if word in model.wv], axis=0)

def calculate_cosine_similarity(vector1, vector2):
    return np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))

def calculate_euclidean_distance(vector1, vector2):
    return np.linalg.norm(vector1 - vector2)

def calculate_manhattan_distance(vector1, vector2):
    return np.sum(np.abs(vector1 - vector2))

logging.info("Calculating cosine similarity between sentences...")
sentence1 = "I love horror movies"
sentence2 = "Romantic comedies are so boring"

vector1_cbow = sentence_vector(sentence1, cbow_model)
vector2_cbow = sentence_vector(sentence2, cbow_model)
cosine_similarity_cbow = calculate_cosine_similarity(vector1_cbow, vector2_cbow)
print("Cosine Similarity between sentences using CBOW model:", cosine_similarity_cbow)

vector1_skipgram = sentence_vector(sentence1, skipgram_model)
vector2_skipgram = sentence_vector(sentence2, skipgram_model)
cosine_similarity_skipgram = calculate_cosine_similarity(vector1_skipgram, vector2_skipgram)
print("Cosine Similarity between sentences using Skip-Gram model:", cosine_similarity_skipgram)

euclidean_distance_cbow = calculate_euclidean_distance(vector1_cbow, vector2_cbow)
print("Euclidean Distance between sentences using CBOW model:", euclidean_distance_cbow)

manhattan_distance_cbow = calculate_manhattan_distance(vector1_cbow, vector2_cbow)
print("Manhattan Distance between sentences using CBOW model:", manhattan_distance_cbow)
#%%

vocab_file_path = "C:/Users/Academy2024/Desktop/fmaric/PROMPTENGINEERING/aclImdb/imdb.vocab"
with open(vocab_file_path, 'r', encoding='utf-8') as f:
    vocab = f.read().splitlines()

words = [word for word in vocab[:200] if word in cbow_model.wv]
word_vectors = [cbow_model.wv[word] for word in words]

word_vectors = np.array(word_vectors)

tsne = TSNE(n_components=2)
word_vectors_tsne = tsne.fit_transform(word_vectors)

plt.figure(figsize=(14, 7))
plt.scatter(word_vectors_tsne[:, 0], word_vectors_tsne[:, 1])
for i, word in enumerate(words):
    plt.annotate(word, xy=(word_vectors_tsne[i, 0], word_vectors_tsne[i, 1]))
plt.title("t-SNE visualization of word embeddings")
plt.show()
#%%

logging.info("Clustering test examples and calculating accuracy...")
def get_sentence_vector(sentence, model):
    words = preprocess_text(sentence)
    return np.mean([model.wv[word] for word in words if word in model.wv], axis=0)

if test_data is None:
    logging.info("Loading test data...")
    test_data = load_data("C:/Users/Academy2024/Desktop/fmaric/PROMPTENGINEERING/aclImdb/test", is_test_data=True)
    logging.info(f"Loaded {len(test_data)} test samples.")
    print("First 5 test samples:", test_data[:5])

if test_data:
    test_vectors = [get_sentence_vector(" ".join(sentence), cbow_model) for sentence in test_data]
    kmeans = KMeans(n_clusters=2, random_state=0).fit(test_vectors)

    true_labels = [1] * (len(test_data) // 2) + [0] * (len(test_data) // 2)
    predicted_labels = kmeans.labels_

    accuracy = accuracy_score(true_labels, predicted_labels)
    print("Classification Accuracy:", accuracy)
else:
    logging.error("Test data is empty. Skipping clustering and accuracy calculation.")
# %%