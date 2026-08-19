import sys
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config
from core.auth.database import init_db
from core.chat.database import init_chat_db
init_db()
init_chat_db()

from core.engine import BaseRAGEngine
engine = BaseRAGEngine(Config)

query = "Summarize the architecture configuration from ai_architecture.txt and the server hardware from hardware_specs.txt."
filter_list = ["ai_architecture.txt", "hardware_specs.txt"]

dense = engine.dense_search(query, k=16, doc_filter=filter_list)
sparse = engine.sparse_search(query, k=16, doc_filter=filter_list)
fusion = engine.reciprocal_rank_fusion(dense, sparse, k=60)

print("Fusion count:", len(fusion))
pairs = [[query, d.page_content] for d in fusion]
raw_scores = engine.reranker.predict(pairs)
print("MIN_RERANK_SCORE in Config:", getattr(Config, "MIN_RERANK_SCORE", None))
print("MIN_RERANK_SCORE_STRICT in Config:", getattr(Config, "MIN_RERANK_SCORE_STRICT", None))
for d, s in zip(fusion, raw_scores):
    print("  - Doc:", d.metadata.get("document_id"), "Reranker Score:", s)
