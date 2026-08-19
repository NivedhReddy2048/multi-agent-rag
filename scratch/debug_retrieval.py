import sys
import traceback
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from config import Config
    from core.auth.database import init_db
    from core.chat.database import init_chat_db
    init_db()
    init_chat_db()

    from core.engine import BaseRAGEngine
    from agents.retrieval import RetrievalAgent

    engine = BaseRAGEngine(Config)
    retrieval = RetrievalAgent(engine)

    print("--- Testing Search B1 ---")
    res1 = retrieval.run({
        "query": "What are the core characteristics of this architecture?",
        "doc_filter": ["ai_architecture.txt"],
        "target_documents": ["ai_architecture.txt"],
        "top_k": 8,
    })
    print("B1 Sources count:", len(res1.sources), "Confidence:", res1.confidence)
    for s in res1.sources:
        print("  - Chunk:", s.get("text"))

    print("\n--- Testing Search B4 ---")
    res4 = retrieval.run({
        "query": "Summarize the architecture configuration and the server hardware.",
        "doc_filter": ["ai_architecture.txt", "hardware_specs.txt"],
        "target_documents": ["ai_architecture.txt", "hardware_specs.txt"],
        "top_k": 8,
    })
    print("B4 Sources count:", len(res4.sources), "Confidence:", res4.confidence)
    for s in res4.sources:
        print("  - Chunk:", s.get("text"), "File:", s.get("source"))

except Exception as e:
    traceback.print_exc()
