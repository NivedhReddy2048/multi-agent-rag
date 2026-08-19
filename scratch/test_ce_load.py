import sys, os, traceback
sys.modules['pyarrow'] = None

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    print("Importing CrossEncoder...", flush=True)
    from sentence_transformers import CrossEncoder
    print("CrossEncoder imported successfully!", flush=True)
    print("Loading model cross-encoder/ms-marco-MiniLM-L-6-v2...", flush=True)
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    print("Model loaded successfully!", flush=True)
    score = model.predict([["Explain Transformers", "Transformers use self-attention mechanism."]])
    print("Predict score:", score, flush=True)
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
