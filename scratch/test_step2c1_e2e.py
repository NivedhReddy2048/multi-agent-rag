import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Config
from core.planner.enums import SourceStrategy
from core.planner.rules import ExecutionPlan
from langchain_core.documents import Document

class MockEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self._last_retrieved_count = 0
        self._last_reranked_count = 0
        self._last_rejected_count = 0
        self._last_min_score_used = 0.0

    def dense_search(self, query, k=8, doc_filter=None):
        return []
    def sparse_search(self, query, k=8, doc_filter=None):
        return []
    def reciprocal_rank_fusion(self, dense, sparse):
        return []

    def rerank(self, query, docs, top_k=6, min_score_override=None):
        min_score = min_score_override if min_score_override is not None else float(getattr(self.cfg, "MIN_RERANK_SCORE", 0.0))
        self._last_retrieved_count = len(docs)
        self._last_reranked_count = len(docs)
        
        scored = []
        for d in docs:
            score = float(d.metadata.get("score", 0.0))
            if score >= min_score:
                scored.append((d, score))
        
        self._last_rejected_count = len(docs) - len(scored)
        self._last_min_score_used = min_score
        return scored[:top_k]

    def compress_context(self, scored_tuples, max_chunks=6):
        return [doc for doc, score in scored_tuples[:max_chunks]]

    def confidence(self):
        return 85

def run_scenarios():
    cfg = Config()
    engine = MockEngine(cfg)
    
    from agents.retrieval import RetrievalAgent
    from agents.crag import CRAGAgent
    from agents.synthesis import SynthesisAgent

    retrieval = RetrievalAgent(engine)
    crag = CRAGAgent(cfg)
    synthesis = SynthesisAgent(cfg)

    print("=== SCENARIO A: GENERAL KNOWLEDGE ===")
    query_a = "Explain the core components of a Transformer."
    borderline_doc = Document(page_content="Deep learning architectures have evolved from early multilayer perceptrons.", metadata={"score": -0.5, "source_file": "overview.txt"})
    irrelevant_doc = Document(page_content="B-tree indexing structures in databases.", metadata={"score": -11.3, "source_file": "db.txt"})

    # Retrieval in GENERAL_KNOWLEDGE mode
    # Monkeypatch fused retrieval
    engine.reciprocal_rank_fusion = lambda d, s: [borderline_doc, irrelevant_doc]

    res_a = retrieval.run({
        "query": query_a,
        "source_strategy": SourceStrategy.GENERAL_KNOWLEDGE,
    })

    print(f"Strategy: {res_a.metadata['source_strategy']}")
    print(f"Min Score Used: {res_a.metadata['min_rerank_score_used']}")
    print(f"Retrieved Chunks: {len(res_a.sources)}")
    print(f"Rejected Count: {res_a.metadata['rejected_by_rerank_count']}")
    
    assert res_a.metadata['min_rerank_score_used'] == 0.0
    assert len(res_a.sources) == 0
    assert res_a.metadata['rejected_by_rerank_count'] == 2
    print("SCENARIO A PASSED!\n")


    print("=== SCENARIO B: STRICT DOCUMENT MODE ===")
    query_b = "Using only my uploaded document, explain the architecture."
    target_doc_chunk = Document(page_content="The uploaded document explains the Transformer architecture relying on self-attention mechanism and multi-head projection layers.", metadata={"score": -0.5, "source_file": "ai_notes.txt"})
    noise_doc_chunk = Document(page_content="Cooking recipe for sourdough bread.", metadata={"score": -11.4, "source_file": "recipe.txt"})

    engine.reciprocal_rank_fusion = lambda d, s: [target_doc_chunk, noise_doc_chunk]

    res_b = retrieval.run({
        "query": query_b,
        "source_strategy": SourceStrategy.DOCUMENT_ONLY,
    })

    print(f"Strategy: {res_b.metadata['source_strategy']}")
    print(f"Min Score Used: {res_b.metadata['min_rerank_score_used']}")
    print(f"Retrieved Chunks: {len(res_b.sources)}")
    print(f"Surviving Score: {res_b.sources[0]['score'] if res_b.sources else None}")
    print(f"Rejected Count: {res_b.metadata['rejected_by_rerank_count']}")

    assert res_b.metadata['min_rerank_score_used'] == -1.0
    assert len(res_b.sources) == 1
    assert res_b.sources[0]['score'] == -0.5
    assert res_b.metadata['rejected_by_rerank_count'] == 1

    # CRAG evaluation on surviving chunk
    is_sufficient, crag_score = crag.evaluate_retrieval(query_b, res_b.sources, source_strategy=SourceStrategy.DOCUMENT_ONLY)
    print(f"CRAG Evaluation Score: {crag_score} | Sufficiency: {is_sufficient}")
    assert is_sufficient is True

    # Synthesis prompt preparation
    exec_plan_b = ExecutionPlan(source_strategy=SourceStrategy.DOCUMENT_ONLY)
    p, inputs, intent, budgeted_docs, q, smode, tname, sys_msg, telem = synthesis._prepare_prompt_and_context({
        "query": query_b,
        "documents": res_b.sources,
        "source_strategy": SourceStrategy.DOCUMENT_ONLY,
        "execution_plan": exec_plan_b,
    })
    print(f"Synthesis Budgeted Chunks: {len(budgeted_docs)}")
    assert len(budgeted_docs) == 1
    print("SCENARIO B PASSED!\n")

if __name__ == "__main__":
    run_scenarios()
    print("ALL END-TO-END SCENARIOS SUCCESSFULLY VERIFIED!")
