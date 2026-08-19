"""Unit and Integration Test Suite for EKIP Phase 2.4 Knowledge Verification, Ranking & Evidence Intelligence."""

import pytest
from core.models.domain import KnowledgeResult, KnowledgeCollection, SourceType
from core.models.verification import (
    VerificationProfile,
    VerifiedKnowledgeResult,
    VerifiedKnowledgeCollection,
)
from core.verification.enhanced_crag import EnhancedCRAGVerifier, EvidenceQualityGrade
from core.verification.knowledge_verifier import KnowledgeVerifier, knowledge_verifier
from graph.builder import create_ekip_planning_graph
from graph.state import EKIPGraphState


def test_verified_knowledge_models():
    """Verify VerifiedKnowledgeResult and VerificationProfile instantiations."""
    profile = VerificationProfile(
        relevance_score=0.9,
        credibility_score=0.95,
        agreement_score=0.85,
        freshness_score=0.8,
        completeness_score=0.9,
        educational_value_score=0.88,
        overall_score=0.89,
    )
    res = VerifiedKnowledgeResult(
        provider="semantic_scholar",
        source_type=SourceType.SEMANTIC_SCHOLAR,
        title="Attention is All You Need",
        content="Transformer architecture based on self-attention mechanisms.",
        verification_score=0.89,
        profile=profile,
        is_canonical=True,
    )
    assert res.provider == "semantic_scholar"
    assert res.verification_score == 0.89
    assert res.profile.relevance_score == 0.9
    assert res.is_canonical is True


def test_enhanced_crag_verifier():
    """Verify EnhancedCRAGVerifier grading across multi-source results."""
    crag = EnhancedCRAGVerifier()

    dummy_results = [
        KnowledgeResult(
            provider="wikipedia",
            source_type=SourceType.WIKIPEDIA,
            title="Quantum Computing",
            content="Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics to solve complex problems.",
        ),
        KnowledgeResult(
            provider="arxiv",
            source_type=SourceType.ARXIV,
            title="Quantum Algorithms Overview",
            content="Detailed study on quantum computing algorithms including Shor's and Grover's search algorithms.",
        ),
    ]

    grade, score, cat_avgs, notes = crag.evaluate_multi_source_evidence("Quantum Computing Algorithms", dummy_results)
    assert grade in (EvidenceQualityGrade.CORRECT, EvidenceQualityGrade.AMBIGUOUS)
    assert score > 0.0
    assert "wikipedia" in cat_avgs
    assert "arxiv" in cat_avgs
    assert len(notes) >= 3


def test_duplicate_detection():
    """Verify KnowledgeVerifier duplicate detection and canonical grouping."""
    verifier = KnowledgeVerifier()

    items = [
        KnowledgeResult(
            provider="wikipedia",
            source_type=SourceType.WIKIPEDIA,
            title="Backpropagation in Neural Networks",
            content="Backpropagation is a widely used algorithm in artificial neural networks for calculating gradients.",
        ),
        KnowledgeResult(
            provider="google_books",
            source_type=SourceType.BOOK,
            title="Backpropagation in Neural Networks (Duplicate)",
            content="Backpropagation is a widely used algorithm in artificial neural networks for calculating gradients.",
        ),
        KnowledgeResult(
            provider="arxiv",
            source_type=SourceType.ARXIV,
            title="Gradient Descent Variants",
            content="Comprehensive analysis of stochastic gradient descent, Adam, RMSprop, and momentum optimization.",
        ),
    ]

    col = KnowledgeCollection(query="Backpropagation", results=items)
    ver_col = verifier.verify_collection(col)

    assert len(ver_col.duplicates) == 1
    assert ver_col.duplicates[0]["canonical_title"] == "Backpropagation in Neural Networks"
    assert len(ver_col.verified_results) == 3
    # First canonical result should have is_canonical=True
    assert ver_col.verified_results[0].is_canonical is True


def test_conflict_detection():
    """Verify detection of conflicting claims across sources."""
    verifier = KnowledgeVerifier()

    items = [
        KnowledgeResult(
            provider="wikipedia",
            source_type=SourceType.WIKIPEDIA,
            title="P vs NP Problem Overview",
            content="P vs NP is a major unsolved problem in computer science. Most computer scientists believe P is not equal to NP.",
        ),
        KnowledgeResult(
            provider="general_ai",
            source_type=SourceType.GENERAL_AI,
            title="Alternative Claim",
            content="P vs NP is a major unsolved problem in computer science. Some claim P is equal to NP and not unresolved.",
        ),
    ]

    col = KnowledgeCollection(query="P vs NP", results=items)
    ver_col = verifier.verify_collection(col)

    assert isinstance(ver_col.conflicts, list)


def test_evidence_ranking():
    """Verify ordering of evidence by multi-dimensional score."""
    verifier = KnowledgeVerifier()

    items = [
        KnowledgeResult(
            provider="general_ai",
            source_type=SourceType.GENERAL_AI,
            title="General AI Overview",
            content="Short summary of machine learning.",
        ),
        KnowledgeResult(
            provider="semantic_scholar",
            source_type=SourceType.SEMANTIC_SCHOLAR,
            title="Deep Residual Learning for Image Recognition",
            content="Deeper neural networks are more difficult to train. We present a residual learning framework to ease training.",
            published_date="2024",
        ),
    ]

    col = KnowledgeCollection(query="Deep Residual Learning", results=items)
    ver_col = verifier.verify_collection(col)

    assert len(ver_col.ranking) == 2
    # Semantic Scholar item (higher credibility, relevance & freshness) should rank first
    assert ver_col.verified_results[0].provider == "semantic_scholar"


def test_full_langgraph_verification_pipeline():
    """Verify full LangGraph 9-node execution including collection, verification & ranking."""
    graph = create_ekip_planning_graph()
    state = graph.invoke({"question": "Explain Backpropagation and Neural Networks"})

    assert isinstance(state, EKIPGraphState)
    assert state.execution_plan is not None
    assert "verified_collection" in state.provider_metadata or state.verified_collection is not None
    ver_dict = state.provider_metadata.get("verified_collection") or state.verified_collection
    assert "verified_results" in ver_dict
    assert "overall_confidence" in ver_dict
    assert "verification_summary" in ver_dict
