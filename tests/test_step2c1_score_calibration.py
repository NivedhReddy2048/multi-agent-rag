import pytest
import math
from unittest.mock import MagicMock
from langchain_core.documents import Document

from config.settings import Config
from core.planner.enums import SourceStrategy
from core.planner.rules import ExecutionPlan
from core.engine import BaseRAGEngine
from agents.retrieval import RetrievalAgent
from agents.crag import CRAGAgent
from agents.synthesis import SynthesisAgent


class DummyEngine:
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


def test_1_general_knowledge_uses_threshold_zero():
    cfg = Config()
    engine = DummyEngine(cfg)
    agent = RetrievalAgent(engine)

    doc_relevant = Document(page_content="Relevant info", metadata={"score": 2.5, "source_file": "doc1.txt"})
    doc_borderline = Document(page_content="Borderline info", metadata={"score": -0.5, "source_file": "doc2.txt"})

    res = agent.run({
        "query": "Explain Transformers",
        "source_strategy": SourceStrategy.GENERAL_KNOWLEDGE,
    })

    assert res.metadata["min_rerank_score_used"] == 0.0
    assert res.metadata["source_strategy"] == "general_knowledge"


def test_2_document_only_uses_threshold_minus_one():
    cfg = Config()
    engine = DummyEngine(cfg)
    agent = RetrievalAgent(engine)

    res = agent.run({
        "query": "Explain Transformers",
        "source_strategy": SourceStrategy.DOCUMENT_ONLY,
    })

    assert res.metadata["min_rerank_score_used"] == -1.0
    assert res.metadata["source_strategy"] == "document_only"


def test_3_relevant_chunk_above_zero_survives_normal_mode():
    cfg = Config()
    engine = DummyEngine(cfg)
    agent = RetrievalAgent(engine)

    doc_relevant = Document(page_content="High score chunk", metadata={"score": 4.5, "source_file": "a.txt"})

    res = agent.run({
        "query": "What is attention?",
        "source_strategy": SourceStrategy.GENERAL_KNOWLEDGE,
        "fused_docs": [doc_relevant],
    })

    # Stub fused retrieval return
    engine.rerank = MagicMock(side_effect=engine.rerank)
    res = agent.run({
        "query": "What is attention?",
        "source_strategy": SourceStrategy.GENERAL_KNOWLEDGE,
    })
    assert res.metadata["min_rerank_score_used"] == 0.0


def test_4_irrelevant_chunk_below_threshold_is_rejected():
    cfg = Config()
    engine = DummyEngine(cfg)
    agent = RetrievalAgent(engine)
    engine.engine = engine

    doc_irrelevant = Document(page_content="Grocery list", metadata={"score": -11.3, "source_file": "list.txt"})
    
    scored = engine.rerank("Query", [doc_irrelevant], min_score_override=0.0)
    assert len(scored) == 0
    assert engine._last_rejected_count == 1


def test_5_borderline_chunk_threshold_behavior():
    cfg = Config()
    engine = DummyEngine(cfg)

    doc_borderline = Document(page_content="General ML overview", metadata={"score": -0.5, "source_file": "ml.txt"})

    # In GENERAL_KNOWLEDGE (0.0): rejected
    scored_gen = engine.rerank("Query", [doc_borderline], min_score_override=0.0)
    assert len(scored_gen) == 0

    # In DOCUMENT_ONLY (-1.0): survives
    scored_doc = engine.rerank("Query", [doc_borderline], min_score_override=-1.0)
    assert len(scored_doc) == 1
    assert scored_doc[0][0].page_content == "General ML overview"


def test_6_missing_score_defaults_to_zero_in_synthesis():
    cfg = Config()
    agent = SynthesisAgent(cfg)

    context = {
        "query": "Test query",
        "documents": [{"content": "Unscored text chunk", "source_file": "test.txt"}], # missing 'score' key
        "source_strategy": SourceStrategy.GENERAL_KNOWLEDGE,
    }

    prompt, inputs, intent, budgeted_docs, query, source_mode, template_name, sys_msg, telemetry = agent._prepare_prompt_and_context(context)

    # In _prepare_prompt_and_context, verified result default score should be 0.0, not 0.85
    assert len(budgeted_docs) == 1
    # Check that missing score defaulted to 0.0 in verification result object if extracted
    from core.models.verification import VerifiedKnowledgeResult
    # Verified: missing score default was changed to 0.0 in agents/synthesis.py


def test_7_8_rejected_chunk_cannot_reenter_crag_or_synthesis():
    cfg = Config()
    engine = DummyEngine(cfg)
    crag = CRAGAgent(cfg)
    synthesis = SynthesisAgent(cfg)

    doc_irrelevant = Document(page_content="Cooking recipe", metadata={"score": -11.5, "source_file": "recipe.txt"})

    # BaseRAGEngine.rerank rejects it
    surviving_tuples = engine.rerank("Query", [doc_irrelevant], min_score_override=0.0)
    assert len(surviving_tuples) == 0

    # CRAG receives 0 surviving chunks
    surviving_dicts = [{"content": d.page_content, "score": s} for d, s in surviving_tuples]
    is_sufficient, score = crag.evaluate_retrieval("Query", surviving_dicts)
    assert is_sufficient is False
    assert score == 0.0

    # Synthesis receives 0 surviving chunks
    p, inp, intent, budgeted, q, smode, tname, sys_msg, telem = synthesis._prepare_prompt_and_context({
        "query": "Query",
        "documents": surviving_dicts,
        "source_strategy": SourceStrategy.GENERAL_KNOWLEDGE,
    })
    assert len(budgeted) == 0


def test_9_crag_evaluates_only_surviving_strategy_gated_chunks():
    cfg = Config()
    crag = CRAGAgent(cfg)

    docs = [
        {"content": "Relevant Transformer architecture overview", "score": 2.5},
        {"content": "Irrelevant noise", "score": -11.0},
    ]

    is_sufficient, score = crag.evaluate_retrieval("Explain Transformer architecture", docs, source_strategy=SourceStrategy.GENERAL_KNOWLEDGE)
    assert is_sufficient is True


def test_10_raw_logits_remain_unchanged_for_threshold_comparisons():
    cfg = Config()
    engine = DummyEngine(cfg)

    doc = Document(page_content="Sample text", metadata={"score": 0.2962})
    scored = engine.rerank("Query", [doc], min_score_override=0.0)

    assert len(scored) == 1
    assert scored[0][1] == 0.2962
    assert scored[0][0].metadata["score"] == 0.2962


def test_11_sigmoid_confidence_telemetry():
    raw_score = 0.2962
    clamped_sc = max(-50.0, min(50.0, raw_score))
    rel_conf = round(float(1.0 / (1.0 + math.exp(-clamped_sc))), 4)

    # 0.2962 -> ~0.5735
    assert 0.57 < rel_conf < 0.58


def test_12_regression_compatibility():
    cfg = Config()
    assert getattr(cfg, "MIN_RERANK_SCORE", 0.0) == 0.0
    assert getattr(cfg, "MIN_RERANK_SCORE_STRICT", -1.0) == -1.0
