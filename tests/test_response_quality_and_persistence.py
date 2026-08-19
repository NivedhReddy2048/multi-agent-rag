"""EKIP Platform Test Suite for save_message Contract, Multi-Turn Persistence, and Response Generation Quality."""

import pytest
import json
from config.settings import Config
from core.models.verification import VerifiedKnowledgeCollection
from core.synthesis import knowledge_synthesizer, response_composer
from core.chat.database import (
    create_chat_session,
    save_message,
    get_chat_messages,
    get_chat_session,
)
from ui.chat_sidebar import start_new_chat, load_chat_session


def test_1_save_message_accepts_rich_response_kwargs(tmp_path):
    """Test 1: Verify save_message accepts rich response fields and **kwargs without TypeError."""
    db_file = str(tmp_path / "test_contract.db")
    sid = create_chat_session("u1", "Contract Test", "Initial Prompt", db_path=db_file)

    # Must accept positional and keyword variations without raising TypeError
    res1 = save_message(
        session_id=sid,
        role="assistant",
        content="Test content",
        citations=[{"title": "Doc1"}],
        agent_trace=["Trace1"],
        confidence=90,
        metadata={"key": "val"},
        db_path=db_file,
    )
    assert res1 is True

    # Flexible kwargs test (chat_id alias, extra parameters)
    res2 = save_message(
        chat_id=sid,
        role="assistant",
        content="Test content 2",
        citations=[{"title": "Doc2"}],
        extra_unexpected_keyword="safe_pass",
        db_path=db_file,
    )
    assert res2 is True


def test_2_round_trip_persistence(tmp_path):
    """Test 2: Save user & assistant message with citations, agent_trace, confidence, metadata, then reload."""
    db_file = str(tmp_path / "test_roundtrip.db")
    sid = create_chat_session("u2", "Roundtrip Test", "Explain RAG", db_path=db_file)

    save_message(sid, "user", "Explain RAG", db_path=db_file)
    save_message(
        sid,
        "assistant",
        "RAG stands for Retrieval-Augmented Generation.",
        citations=[{"title": "RAG Paper", "url": "https://example.com/rag"}],
        agent_trace=["PlannerNode", "SynthesizerNode"],
        confidence=96,
        metadata={"source_mode": "documents", "educational_response": {"summary": "RAG overview"}},
        db_path=db_file,
    )

    history = get_chat_messages(sid, db_path=db_file)
    assert len(history) == 2

    user_msg = history[0]
    assert user_msg["role"] == "user"
    assert user_msg["content"] == "Explain RAG"

    asst_msg = history[1]
    assert asst_msg["role"] == "assistant"
    assert "Retrieval-Augmented" in asst_msg["content"]
    assert asst_msg["confidence"] == 96
    assert len(asst_msg["citations"]) == 1
    assert asst_msg["citations"][0]["title"] == "RAG Paper"
    assert asst_msg["agent_trace"] == ["PlannerNode", "SynthesizerNode"]
    assert asst_msg["metadata"]["educational_response"]["summary"] == "RAG overview"


def test_3_multi_turn_conversation_ordering(tmp_path):
    """Test 3: Multi-turn (3 user + 3 assistant) conversation saved and restored in exact order."""
    db_file = str(tmp_path / "test_multi_turn.db")
    sid = create_chat_session("u3", "Multi-turn Test", "Prompt 1", db_path=db_file)

    turns = [
        ("Explain Transformer architectures.", "Transformers use self-attention mechanism."),
        ("What is self-attention?", "Self-attention computes representations by relating different positions."),
        ("Explain multi-head attention.", "Multi-head attention projects queries, keys, and values into subspaces."),
    ]

    for idx, (user_q, asst_a) in enumerate(turns, start=1):
        save_message(sid, "user", user_q, db_path=db_file)
        save_message(
            sid,
            "assistant",
            asst_a,
            citations=[{"title": f"Doc {idx}"}],
            confidence=90 + idx,
            db_path=db_file,
        )

    history = get_chat_messages(sid, db_path=db_file)
    assert len(history) == 6

    # Verify exact ordering: User1, Asst1, User2, Asst2, User3, Asst3
    expected_roles = ["user", "assistant", "user", "assistant", "user", "assistant"]
    assert [m["role"] for m in history] == expected_roles
    assert history[0]["content"] == turns[0][0]
    assert history[1]["content"] == turns[0][1]
    assert history[2]["content"] == turns[1][0]
    assert history[3]["content"] == turns[1][1]
    assert history[4]["content"] == turns[2][0]
    assert history[5]["content"] == turns[2][1]


def test_4_new_chat_and_history_switching(tmp_path):
    """Test 4: Creating a New Chat makes it active, returning to previous chat restores full history."""
    db_file = str(tmp_path / "test_new_chat.db")
    
    # Create Chat A
    sid_a = create_chat_session("u4", "Chat A", "First Message A", db_path=db_file)
    save_message(sid_a, "user", "First Message A", db_path=db_file)
    save_message(sid_a, "assistant", "Response A", confidence=95, db_path=db_file)

    # Create Chat B
    sid_b = create_chat_session("u4", "Chat B", "First Message B", db_path=db_file)
    save_message(sid_b, "user", "First Message B", db_path=db_file)
    save_message(sid_b, "assistant", "Response B", confidence=92, db_path=db_file)

    # Verify Chat A history
    history_a = get_chat_messages(sid_a, db_path=db_file)
    assert len(history_a) == 2
    assert history_a[0]["content"] == "First Message A"
    assert history_a[1]["content"] == "Response A"

    # Verify Chat B history
    history_b = get_chat_messages(sid_b, db_path=db_file)
    assert len(history_b) == 2
    assert history_b[0]["content"] == "First Message B"
    assert history_b[1]["content"] == "Response B"


def test_5_deprecated_model_protection():
    """Test 5: Deprecated models (llama-3.3-70b-versatile, llama-3.1-8b-instant) are not active defaults."""
    assert Config.GROQ_MODEL != "llama-3.3-70b-versatile"
    assert Config.GROQ_MODEL != "llama-3.1-8b-instant"
    assert Config.LLM_MODEL != "llama-3.3-70b-versatile"
    assert "llama-3.3-70b-versatile" not in Config.GROQ_MODELS


def test_6_response_generation_quality():
    """Test 6: Explain Concept synthesis returns rich educational explanation without errors."""
    coll = VerifiedKnowledgeCollection(
        query="Explain the core concepts of Transformer architectures in Machine Learning.",
        execution_plan_id="",
        verification_timestamp="",
        total_latency_ms=0,
        verified_results=[],
    )
    synth = knowledge_synthesizer.synthesize(coll)
    resp = response_composer.compose_response(synth, coll)

    assert len(resp.ai_explanation) > 500
    assert "Transformer" in resp.ai_explanation or "architecture" in resp.ai_explanation.lower()
    assert synth.confidence > 0.0
