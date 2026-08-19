import sys, os, traceback
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    print("Importing AutoTokenizer & AutoModelForSequenceClassification...", flush=True)
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    print(f"Loading tokenizer & model: {model_name}...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    print("Model loaded successfully!", flush=True)

    query = "Explain Transformers"
    doc = "Transformers use self-attention mechanism."
    features = tokenizer([query], [doc], padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        scores = model(**features).logits.flatten()
    print("Logit score:", scores.item(), flush=True)
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
