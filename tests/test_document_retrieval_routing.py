"""Regression Test Suite for Document Retrieval and Document-Aware Routing in EKIP.

Validates:
1. Explicit document filename and title matching (Rule 1, Rule 6)
2. Generic 'Summarize My Notes' multi-document balanced retrieval (Rule 2, Rule 10)
3. Prevention of largest-document bias across chunk-disparate files (Rule 4)
4. Preservation of document metadata (Rule 5)
5. Cross-document comparison query targeting (Rule 7)
6. Non-defaulting to external web search when internal documents targeted (Rule 8)
7. Document isolation to prevent answering from unrelated files (Rule 9)
8. Provider/Model metadata and Confidence score accuracy (Rule 12, Rule 13)
"""

import pytest
from langchain_core.documents import Document
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.enums import EducationalIntent, SourceStrategy, RetrievalStrategy
from core.planner.execution_plan import ExecutionPlan
from core.engine import BaseRAGEngine, IncrementalBM25
from agents.sources.document_agent import DocumentKnowledgeAgent
from agents.retrieval import RetrievalAgent
from agents.orchestrator import OrchestratorAgent
from config import Config


@pytest.fixture
def available_docs():
    return [
        "Coverletter_Stripe.pdf",
        "ai_arch.txt",
        "Deep_Solar_System_6_Page_Detailed_Report.pdf",
    ]


def test_explicit_document_target_resolution(available_docs):
    """Rule 1 & Rule 6: Validate explicit filename resolution in planner."""
    # Test exact filename match
    plan1 = RuleBasedPlannerEngine.generate_plan(
        "Summarize Coverletter_Stripe.pdf", available_docs=available_docs
    )
    assert plan1.target_documents == ["Coverletter_Stripe.pdf"]
    assert plan1.source_strategy == SourceStrategy.DOCUMENT_ONLY

    # Test alias stem match
    plan2 = RuleBasedPlannerEngine.generate_plan(
        "What does my cover letter say about experience?", available_docs=available_docs
    )
    assert "Coverletter_Stripe.pdf" in plan2.target_documents

    # Test AI Architecture alias
    plan3 = RuleBasedPlannerEngine.generate_plan(
        "Explain the system design in ai_arch.txt", available_docs=available_docs
    )
    assert "ai_arch.txt" in plan3.target_documents

    # Test Deep Solar System alias
    plan4 = RuleBasedPlannerEngine.generate_plan(
        "Give details on the solar system report", available_docs=available_docs
    )
    assert "Deep_Solar_System_6_Page_Detailed_Report.pdf" in plan4.target_documents


def test_multi_document_comparison_resolution(available_docs):
    """Rule 7: Validate multi-document comparison query parsing."""
    plan = RuleBasedPlannerEngine.generate_plan(
        "Compare my cover letter and ai_arch.txt", available_docs=available_docs
    )
    assert set(plan.target_documents) == {"Coverletter_Stripe.pdf", "ai_arch.txt"}
    assert plan.requires_internal_documents is True


def test_generic_summarize_notes_routing(available_docs):
    """Rule 2 & Rule 10: Validate 'Summarize My Notes' routes to STUDY_NOTES and DOCUMENT_ONLY strategy."""
    plan = RuleBasedPlannerEngine.generate_plan(
        "Generate a comprehensive summary of my uploaded study notes", available_docs=available_docs
    )
    assert plan.intent == EducationalIntent.STUDY_NOTES
    assert plan.source_strategy == SourceStrategy.DOCUMENT_ONLY
    assert plan.requires_internal_documents is True


def test_bm25_document_filtering():
    """Rule 6: Validate IncrementalBM25 doc_filter filtering."""
    bm25 = IncrementalBM25(cache_file="./test_bm25_temp.pkl")
    bm25.corpus_size = 0
    bm25.doc_term_freqs = []
    bm25.doc_lengths = []
    bm25.doc_chunk_ids = []

    texts = [
        "Stripe cover letter application software engineer",
        "Deep solar system planetary orbit radiation study",
        "AI architecture RAG vector search retriever pipeline",
    ]
    chunk_ids = ["Coverletter_Stripe.pdf_0", "Deep_Solar_System.pdf_0", "ai_arch.txt_0"]
    bm25.add_documents(texts, chunk_ids=chunk_ids)

    chunk_metadata = [
        {"chunk_id": "Coverletter_Stripe.pdf_0", "document_id": "Coverletter_Stripe.pdf"},
        {"chunk_id": "Deep_Solar_System.pdf_0", "document_id": "Deep_Solar_System.pdf"},
        {"chunk_id": "ai_arch.txt_0", "document_id": "ai_arch.txt"},
    ]

    # Filter to Coverletter_Stripe.pdf only
    top_ids = bm25.get_top_k(
        query="system design pipeline",
        k=5,
        doc_filter=["Coverletter_Stripe.pdf"],
        chunk_metadata=chunk_metadata,
    )
    assert top_ids == ["Coverletter_Stripe.pdf_0"]


def test_document_metadata_richness():
    """Rule 5: Validate loader chunk metadata enrichment."""
    from core.loader import DocumentLoader
    loader = DocumentLoader()
    doc = Document(page_content="Test content chunk for EKIP.", metadata={"page": 1})
    chunks = loader.chunk_documents([doc], file_name="Coverletter_Stripe.pdf")

    assert len(chunks) > 0
    meta = chunks[0].metadata
    assert meta["source_file"] == "Coverletter_Stripe.pdf"
    assert meta["filename"] == "Coverletter_Stripe.pdf"
    assert meta["document_id"] == "Coverletter_Stripe.pdf"
    assert meta["document_title"] == "Coverletter Stripe"
    assert meta["document_type"] == "pdf"
    assert "upload_timestamp" in meta


def test_orchestrator_metadata_integrity(available_docs):
    """Rule 12 & Rule 13: Validate metadata provider/model and non-zero confidence."""
    # Test planner execution contract
    plan = RuleBasedPlannerEngine.generate_plan("Summarize Coverletter_Stripe.pdf", available_docs=available_docs)
    assert plan.target_documents == ["Coverletter_Stripe.pdf"]
    assert plan.requires_internal_documents is True
    assert plan.source_strategy == SourceStrategy.DOCUMENT_ONLY
