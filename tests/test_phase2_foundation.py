"""Tests for EKIP Phase 2.1 Foundation Migration Components."""

import pytest
from config.settings import Config
from graph.state import EKIPGraphState
from graph.builder import create_ekip_graph
from core.models import (
    KnowledgeSource, SourceType, KnowledgeResult,
    ResearchPaper, BookRecommendation, VideoRecommendation,
    LearningSummary, RecommendedQuestion
)
from core.interfaces import (
    KnowledgePlanner, KnowledgeRouter, KnowledgeVerifier,
    KnowledgeRanker, LearningSummarizer
)
from core.memory import ConversationMemory


def test_rebranding_config_title():
    """Verify application title and tagline rebrand in Config."""
    assert "Educational Knowledge Intelligence Platform" in Config.APP_TITLE
    assert "Learn from Multiple Trusted Knowledge Sources" in Config.APP_TAGLINE


def test_langgraph_state_instantiation():
    """Verify EKIPGraphState contains all required multi-source fields."""
    state = EKIPGraphState(question="Explain transformers")
    assert state.question == "Explain transformers"
    assert state.intent in ("general", "concept_explanation")

    assert isinstance(state.retrieved_documents, list)
    assert isinstance(state.retrieved_web, list)
    assert isinstance(state.retrieved_research, list)
    assert isinstance(state.retrieved_books, list)
    assert isinstance(state.retrieved_videos, list)
    assert isinstance(state.retrieved_wikipedia, list)
    assert isinstance(state.recommended_questions, list)


def test_langgraph_builder_instantiation():
    """Verify graph builder skeleton initializes correctly."""
    builder = create_ekip_graph()
    assert builder.is_compiled is True
    res = builder.invoke({"question": "What is CRAG?"})
    assert res.question == "What is CRAG?"


def test_educational_domain_models():
    """Verify domain models instantiate correctly."""
    src = KnowledgeSource(
        source_id="arxiv_123",
        name="arXiv RAG Paper",
        source_type=SourceType.RESEARCH_PAPER,
        provider="arxiv"
    )
    assert src.provider == "arxiv"

    paper = ResearchPaper(
        title="Attention Is All You Need",
        description="Transformer paper",
        source_provider="arxiv",
        authors=["Vaswani et al."],
        year=2017
    )
    assert paper.resource_type == "research_paper"
    assert paper.year == 2017

    book = BookRecommendation(
        title="Deep Learning",
        description="Goodfellow book",
        source_provider="google_books",
        authors=["Ian Goodfellow"]
    )
    assert book.resource_type == "book"

    video = VideoRecommendation(
        title="Neural Networks",
        description="3Blue1Brown series",
        source_provider="youtube",
        video_url="https://youtube.com/watch?v=123"
    )
    assert video.resource_type == "video"


def test_memory_schema_extensions(tmp_path):
    """Verify conversation memory initializes schema with educational metadata support."""
    db_file = str(tmp_path / "test_ekip_mem.db")
    mem = ConversationMemory(db_file)
    cid = mem.create_conversation("Educational Session")
    assert cid is not None
    mem.add_message(
        conversation_id=cid,
        role="user",
        content="Hello EKIP",
        metadata={"learning_path": "AI_Engineer", "learning_level": "advanced"}
    )
    msgs = mem.get_messages(cid)
    assert len(msgs) == 1
    assert msgs[0]["metadata"].get("learning_path") == "AI_Engineer"
