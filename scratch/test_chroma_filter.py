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

print("--- Testing Chroma $or filter ---")
try:
    res = engine.vector_db.similarity_search_with_score(
        "Summarize architecture and server hardware",
        k=8,
        filter={"$or": [{"document_id": "ai_architecture.txt"}, {"document_id": "hardware_specs.txt"}]}
    )
    print("Found docs count:", len(res))
    for d, s in res:
        print("  - Doc:", d.metadata.get("document_id"), "Score:", s)
except Exception as e:
    print("Error with $or:", e)
