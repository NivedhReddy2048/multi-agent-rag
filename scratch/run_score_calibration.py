import sys
import os
import json
import math
import torch
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from transformers import AutoTokenizer, AutoModelForSequenceClassification

print("Loading production CrossEncoder model weights: cross-encoder/ms-marco-MiniLM-L-6-v2...")
model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
model.eval()
print("Model loaded successfully!\n")

def get_cross_encoder_logits(pairs):
    queries = [p[0] for p in pairs]
    chunks = [p[1] for p in pairs]
    features = tokenizer(queries, chunks, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        logits = model(**features).logits.flatten()
    return logits.numpy()

# Evaluation Dataset: 15 Relevant, 15 Irrelevant, 10 Borderline
dataset = [
    # --- 15 RELEVANT PAIRS ---
    {
        "id": "R1",
        "category": "RELEVANT",
        "query": "Explain the core concepts of Transformer architectures in Machine Learning.",
        "chunk": "The Transformer architecture relies on a multi-head self-attention mechanism, allowing parallel processing of sequential text inputs without recurrent connections.",
        "label": 1
    },
    {
        "id": "R2",
        "category": "RELEVANT",
        "query": "Explain the core concepts of Transformer architectures in Machine Learning.",
        "chunk": "In Transformer models, Query, Key, and Value matrices are projected to compute dot-product self-attention weights across tokens.",
        "label": 1
    },
    {
        "id": "R3",
        "category": "RELEVANT",
        "query": "How does backpropagation work in neural networks?",
        "chunk": "Backpropagation calculates gradients of the loss function with respect to weights using the chain rule, enabling gradient descent updates across layers.",
        "label": 1
    },
    {
        "id": "R4",
        "category": "RELEVANT",
        "query": "What is B-tree indexing in relational databases?",
        "chunk": "A B-tree index maintains balanced self-sorting node trees that allow logarithmic time searches, insertions, and deletions in database engines.",
        "label": 1
    },
    {
        "id": "R5",
        "category": "RELEVANT",
        "query": "Explain overfitting and underfitting in machine learning models.",
        "chunk": "Overfitting occurs when a model learns noise and training set specifics, failing to generalize to unseen test data, whereas underfitting means the model is too simple.",
        "label": 1
    },
    {
        "id": "R6",
        "category": "RELEVANT",
        "query": "What is CPU round-robin scheduling in operating systems?",
        "chunk": "Round-robin scheduling allocates a fixed time quantum to each process in the ready queue, context switching processes sequentially when their quantum expires.",
        "label": 1
    },
    {
        "id": "R7",
        "category": "RELEVANT",
        "query": "Explain Convolutional Neural Networks (CNNs) for computer vision.",
        "chunk": "CNNs utilize spatial convolution filters and pooling layers to extract hierarchical visual features such as edges, textures, and objects from images.",
        "label": 1
    },
    {
        "id": "R8",
        "category": "RELEVANT",
        "query": "What is quantum entanglement in physics?",
        "chunk": "Quantum entanglement is a phenomenon where physical states of two or more particles become interconnected such that measuring one instantaneously determines the other.",
        "label": 1
    },
    {
        "id": "R9",
        "category": "RELEVANT",
        "query": "Explain microservices architecture principles.",
        "chunk": "Microservices architecture decomposes monolithic applications into independent, loosely coupled services communicating via APIs or event brokers.",
        "label": 1
    },
    {
        "id": "R10",
        "category": "RELEVANT",
        "query": "What is Gradient Descent in deep learning?",
        "chunk": "Gradient descent is an iterative optimization algorithm that updates parameter weights in the opposite direction of the loss function gradient to minimize error.",
        "label": 1
    },
    {
        "id": "R11",
        "category": "RELEVANT",
        "query": "Explain ACID properties in database transactions.",
        "chunk": "ACID stands for Atomicity, Consistency, Isolation, and Durability, guaranteeing reliable processing of database transactions.",
        "label": 1
    },
    {
        "id": "R12",
        "category": "RELEVANT",
        "query": "What is the purpose of positional encoding in Transformers?",
        "chunk": "Because Transformers process all tokens simultaneously without recurrence, positional encoding adds sinusoidal vectors to token embeddings to encode sequence order.",
        "label": 1
    },
    {
        "id": "R13",
        "category": "RELEVANT",
        "query": "Explain virtual memory and page faults in OS.",
        "chunk": "Virtual memory abstracts physical RAM using page tables; when a process accesses a page not present in RAM, a hardware page fault triggers page loading from disk.",
        "label": 1
    },
    {
        "id": "R14",
        "category": "RELEVANT",
        "query": "What is residual connection in ResNet architectures?",
        "chunk": "Residual connections add skip identity mappings around convolutional blocks, allowing gradients to flow directly during backpropagation and enabling deep networks.",
        "label": 1
    },
    {
        "id": "R15",
        "category": "RELEVANT",
        "query": "Explain REST API design principles.",
        "chunk": "RESTful APIs use HTTP methods (GET, POST, PUT, DELETE) and stateless resource representations (JSON) to facilitate communication between web clients and servers.",
        "label": 1
    },

    # --- 15 IRRELEVANT PAIRS ---
    {
        "id": "I1",
        "category": "IRRELEVANT",
        "query": "Explain the core concepts of Transformer architectures in Machine Learning.",
        "chunk": "B-tree indexing structures optimize relational database query execution speeds by balancing leaf node pointers.",
        "label": 0
    },
    {
        "id": "I2",
        "category": "IRRELEVANT",
        "query": "Explain the core concepts of Transformer architectures in Machine Learning.",
        "chunk": "Microservices communicate asynchronously via AMQP event buses, API gateways, and distributed message queues.",
        "label": 0
    },
    {
        "id": "I3",
        "category": "IRRELEVANT",
        "query": "How does backpropagation work in neural networks?",
        "chunk": "Operating system CPU scheduling uses round-robin and multi-level feedback queues to manage process prioritization.",
        "label": 0
    },
    {
        "id": "I4",
        "category": "IRRELEVANT",
        "query": "What is B-tree indexing in relational databases?",
        "chunk": "Weekly grocery shopping list: apples, whole milk, organic sourdough bread, olive oil, and coffee beans.",
        "label": 0
    },
    {
        "id": "I5",
        "category": "IRRELEVANT",
        "query": "Explain overfitting and underfitting in machine learning models.",
        "chunk": "Baking chocolate chip cookies requires preheating oven to 375 degrees Fahrenheit and mixing butter with granulated sugar.",
        "label": 0
    },
    {
        "id": "I6",
        "category": "IRRELEVANT",
        "query": "What is CPU round-robin scheduling in operating systems?",
        "chunk": "The capital city of France is Paris, famous for the Eiffel Tower, the Louvre museum, and Notre-Dame Cathedral.",
        "label": 0
    },
    {
        "id": "I7",
        "category": "IRRELEVANT",
        "query": "Explain Convolutional Neural Networks (CNNs) for computer vision.",
        "chunk": "Financial accounting rules state that double-entry bookkeeping requires debit and credit entries to balance for every transaction.",
        "label": 0
    },
    {
        "id": "I8",
        "category": "IRRELEVANT",
        "query": "What is quantum entanglement in physics?",
        "chunk": "PostgreSQL database configuration settings for max_connections, shared_buffers, and work_mem tuning.",
        "label": 0
    },
    {
        "id": "I9",
        "category": "IRRELEVANT",
        "query": "Explain microservices architecture principles.",
        "chunk": "Photosynthesis is the process by which green plants convert light energy into chemical energy stored in glucose molecules.",
        "label": 0
    },
    {
        "id": "I10",
        "category": "IRRELEVANT",
        "query": "What is Gradient Descent in deep learning?",
        "chunk": "Car maintenance guidelines recommend changing engine oil every 5000 miles and inspecting tire inflation pressure monthly.",
        "label": 0
    },
    {
        "id": "I11",
        "category": "IRRELEVANT",
        "query": "Explain ACID properties in database transactions.",
        "chunk": "Solar power systems convert sunlight into electricity using photovoltaic solar panels connected to inverter units.",
        "label": 0
    },
    {
        "id": "I12",
        "category": "IRRELEVANT",
        "query": "What is the purpose of positional encoding in Transformers?",
        "chunk": "B-tree indexing maintains balanced leaf nodes for disk block retrieval in file systems and relational engines.",
        "label": 0
    },
    {
        "id": "I13",
        "category": "IRRELEVANT",
        "query": "Explain virtual memory and page faults in OS.",
        "chunk": "Supervised learning algorithm classification using decision tree splitting criteria based on Gini impurity.",
        "label": 0
    },
    {
        "id": "I14",
        "category": "IRRELEVANT",
        "query": "What is residual connection in ResNet architectures?",
        "chunk": "Tennis grand slam tournaments include the Australian Open, French Open, Wimbledon, and US Open.",
        "label": 0
    },
    {
        "id": "I15",
        "category": "IRRELEVANT",
        "query": "Explain REST API design principles.",
        "chunk": "Quantum mechanical wave function collapse under Copenhagen interpretation of subatomic observation.",
        "label": 0
    },

    # --- 10 BORDERLINE PAIRS ---
    {
        "id": "B1",
        "category": "BORDERLINE",
        "query": "Explain Transformer architecture in Machine Learning.",
        "chunk": "Deep learning architectures have evolved from early multilayer perceptrons to complex deep networks used in artificial intelligence applications.",
        "label": 0
    },
    {
        "id": "B2",
        "category": "BORDERLINE",
        "query": "Explain Transformer architecture in Machine Learning.",
        "chunk": "Natural Language Processing utilizes tokenization, stemming, and vector embeddings to represent text corpus inputs.",
        "label": 0
    },
    {
        "id": "B3",
        "category": "BORDERLINE",
        "query": "What is B-tree indexing in relational databases?",
        "chunk": "Database management systems store data on disk and utilize buffer pools to manage memory caches efficiently.",
        "label": 0
    },
    {
        "id": "B4",
        "category": "BORDERLINE",
        "query": "How does backpropagation work in neural networks?",
        "chunk": "Artificial neural networks consist of connected nodes or artificial neurons organized into input, hidden, and output layers.",
        "label": 0
    },
    {
        "id": "B5",
        "category": "BORDERLINE",
        "query": "Explain overfitting and underfitting in machine learning models.",
        "chunk": "Machine learning model evaluation relies on splitting datasets into training, validation, and test subsets.",
        "label": 0
    },
    {
        "id": "B6",
        "category": "BORDERLINE",
        "query": "What is CPU round-robin scheduling in operating systems?",
        "chunk": "Operating systems manage hardware resources including CPU, RAM, disk storage, and input-output peripheral devices.",
        "label": 0
    },
    {
        "id": "B7",
        "category": "BORDERLINE",
        "query": "What is quantum entanglement in physics?",
        "chunk": "Quantum mechanics explores subatomic physical phenomena including wave-particle duality and uncertainty principles.",
        "label": 0
    },
    {
        "id": "B8",
        "category": "BORDERLINE",
        "query": "Explain microservices architecture principles.",
        "chunk": "Software engineering design patterns provide reusable templates for object-oriented component architecture.",
        "label": 0
    },
    {
        "id": "B9",
        "category": "BORDERLINE",
        "query": "Explain REST API design principles.",
        "chunk": "Web development relies on client-server networking protocols including HTTP, HTTPS, and TCP/IP sockets.",
        "label": 0
    },
    {
        "id": "B10",
        "category": "BORDERLINE",
        "query": "What is residual connection in ResNet architectures?",
        "chunk": "Deep neural networks suffer from vanishing gradient problems when trained with many hidden layers.",
        "label": 0
    },
]

# Run CrossEncoder scoring
pairs = [[item["query"], item["chunk"]] for item in dataset]
scores = get_cross_encoder_logits(pairs)

# Store results
for item, score in zip(dataset, scores):
    score_val = float(score)
    item["raw_score"] = score_val
    item["sigmoid_score"] = float(1.0 / (1.0 + math.exp(-score_val)))

# Group scores by category
rel_scores = [item["raw_score"] for item in dataset if item["category"] == "RELEVANT"]
irr_scores = [item["raw_score"] for item in dataset if item["category"] == "IRRELEVANT"]
bor_scores = [item["raw_score"] for item in dataset if item["category"] == "BORDERLINE"]
all_scores = [item["raw_score"] for item in dataset]

def calc_stats(arr):
    arr = np.array(arr)
    return {
        "min": round(float(np.min(arr)), 4),
        "max": round(float(np.max(arr)), 4),
        "mean": round(float(np.mean(arr)), 4),
        "median": round(float(np.median(arr)), 4),
        "std": round(float(np.std(arr)), 4),
        "p10": round(float(np.percentile(arr, 10)), 4),
        "p25": round(float(np.percentile(arr, 25)), 4),
        "p50": round(float(np.percentile(arr, 50)), 4),
        "p75": round(float(np.percentile(arr, 75)), 4),
        "p90": round(float(np.percentile(arr, 90)), 4),
    }

stats = {
    "RELEVANT": calc_stats(rel_scores),
    "BORDERLINE": calc_stats(bor_scores),
    "IRRELEVANT": calc_stats(irr_scores),
    "ALL": calc_stats(all_scores)
}

# Threshold Sweep across candidate thresholds
candidate_thresholds = [-2.0, -1.0, -0.5, 0.0, 0.25, 0.5, 1.0, 2.0]

sweep_results = []

for thresh in candidate_thresholds:
    tp = sum(1 for item in dataset if item["label"] == 1 and item["raw_score"] >= thresh)
    fp = sum(1 for item in dataset if item["label"] == 0 and item["raw_score"] >= thresh)
    tn = sum(1 for item in dataset if item["label"] == 0 and item["raw_score"] < thresh)
    fn = sum(1 for item in dataset if item["label"] == 1 and item["raw_score"] < thresh)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    sweep_results.append({
        "threshold": thresh,
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "FPR": round(fpr, 4),
        "FNR": round(fnr, 4),
    })

results_data = {
    "statistics": stats,
    "threshold_sweep": sweep_results,
    "items": dataset
}

with open("scratch/calibration_results.json", "w", encoding="utf-8") as f:
    json.dump(results_data, f, indent=2)

print("CALIBRATION ANALYSIS COMPLETE!\n")
print("SCORE DISTRIBUTION SUMMARY:")
for cat, s in stats.items():
    print(f"[{cat:<10}] Min: {s['min']:<7.2f} | P25: {s['p25']:<7.2f} | Median: {s['median']:<7.2f} | Mean: {s['mean']:<7.2f} | P75: {s['p75']:<7.2f} | Max: {s['max']:<7.2f}")

print("\nTHRESHOLD SWEEP SUMMARY:")
print(f"{'Threshold':<10} | {'TP':<4} | {'FP':<4} | {'TN':<4} | {'FN':<4} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'FPR':<10} | {'FNR':<10}")
print("-" * 90)
for r in sweep_results:
    print(f"{r['threshold']:<10} | {r['TP']:<4} | {r['FP']:<4} | {r['TN']:<4} | {r['FN']:<4} | {r['precision']:<10.4f} | {r['recall']:<10.4f} | {r['f1']:<10.4f} | {r['FPR']:<10.4f} | {r['FNR']:<10.4f}")
