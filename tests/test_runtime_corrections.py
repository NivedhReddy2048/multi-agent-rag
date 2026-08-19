"""Automated Verification Suite for EKIP 4 Runtime Regression Fixes."""

import pytest
from core.planner.enums import EducationalIntent, SourceStrategy
from core.planner.rules import RuleBasedPlannerEngine
from agents.sources.youtube_agent import YoutubeKnowledgeAgent
from core.synthesis.guided_learning import extract_canonical_topic, guided_learning_engine
from core.synthesis.response_composer import response_composer
from core.models.domain import KnowledgeCollection, KnowledgeResult, SourceType
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult, VerificationProfile


def test_problem_1_video_intent_and_url_preservation():
    """Verify video intent classification and real URL preservation."""
    q1 = "Recommend top learning video concepts for understanding neural networks"
    intent, _ = RuleBasedPlannerEngine.classify_intent(q1, [])
    assert intent == EducationalIntent.VIDEO_RECOMMENDATION

    sources, _ = RuleBasedPlannerEngine.select_sources(q1, intent, None)
    assert SourceType.VIDEO in sources

    agent = YoutubeKnowledgeAgent()
    agent.initialize()
    results = agent.execute(q1, max_results=3)

    assert len(results) > 0
    for res in results:
        assert res.source_type == SourceType.VIDEO
        assert res.url is not None
        assert res.url.startswith("http://") or res.url.startswith("https://")


def test_problem_3_canonical_topic_extraction():
    """Verify topic extraction strips request filler words and avoids stop topics like 'Need'."""
    q_discipline = "I need a YouTube video that explains discipline"
    topic_discipline = extract_canonical_topic(q_discipline)
    assert topic_discipline == "Discipline"
    assert topic_discipline.lower() != "need"
    assert topic_discipline.lower() != "video"

    q_nn = "Recommend top learning video concepts for understanding neural networks"
    topic_nn = extract_canonical_topic(q_nn)
    assert topic_nn == "Neural Networks"

    lpath_discipline = guided_learning_engine.generate_learning_path(q_discipline)
    assert lpath_discipline.current_topic == "Discipline"
    assert "Need" not in lpath_discipline.current_topic


def test_problem_4_context_aware_guided_questions():
    """Verify guided questions are strictly relevant to the canonical topic."""
    q_discipline = "I need a YouTube video that explains discipline"
    gq_discipline = guided_learning_engine.generate_guided_questions(q_discipline)
    assert len(gq_discipline) == 3
    # Must NOT contain backpropagation
    for q in gq_discipline:
        assert "backpropagation" not in q.lower()
        assert "cnn" not in q.lower()
    
    # Must be about discipline
    all_text = " ".join(gq_discipline).lower()
    assert "discipline" in all_text or "habit" in all_text or "consistency" in all_text

    q_nn = "Recommend top learning video concepts for understanding neural networks"
    gq_nn = guided_learning_engine.generate_guided_questions(q_nn)
    assert len(gq_nn) == 3
    nn_text = " ".join(gq_nn).lower()
    assert "backpropagation" in nn_text or "neural" in nn_text or "activation" in nn_text


def test_response_composer_integration():
    """Verify response composer integrates videos, canonical topic, and guided questions."""
    query = "I need a YouTube video that explains discipline"
    res = KnowledgeResult(
        provider="youtube",
        source_type=SourceType.VIDEO,
        title="Video: Understanding Discipline",
        content="Educational lecture on self-discipline and consistency.",
        url="https://www.youtube.com/watch?v=sample123",
        authors=["Learning Channel"],
    )
    v_item = VerifiedKnowledgeResult(
        **res.dict(),
        verification_score=0.9,
        relevance_score=0.9,
        credibility_score=0.9,
        freshness_score=0.9,
        agreement_score=0.9,
        profile=VerificationProfile(overall_score=0.9),
    )
    col = VerifiedKnowledgeCollection(
        query=query,
        overall_confidence=0.9,
        verified_results=[v_item]
    )
    
    from core.models.synthesis import SynthesizedKnowledge
    syn = SynthesizedKnowledge(
        query=query,
        primary_explanation="Self-discipline is the ability to push yourself forward.",
        confidence=0.9,
    )
    
    edu_resp = response_composer.compose_response(syn, col)
    assert len(edu_resp.videos) == 1
    assert edu_resp.videos[0]["url"] == "https://www.youtube.com/watch?v=sample123"
    assert edu_resp.learning_path.current_topic == "Discipline"
    assert len(edu_resp.guided_questions) == 3
    assert "backpropagation" not in " ".join(edu_resp.guided_questions).lower()
