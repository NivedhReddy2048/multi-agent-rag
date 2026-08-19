"""Unit and Integration Test Suite for EKIP Phase 2.5 Knowledge Synthesis, Response Composition & Guided Learning."""

import pytest
from core.models.domain import KnowledgeResult, KnowledgeCollection, SourceType
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult, VerificationProfile
from core.models.synthesis import SynthesizedKnowledge, EducationalResponse, LearningPath
from core.synthesis.knowledge_synthesizer import KnowledgeSynthesizer, knowledge_synthesizer
from core.synthesis.prompt_builder import EducationalPromptBuilder
from core.synthesis.response_composer import ResponseComposer, response_composer
from core.synthesis.guided_learning import GuidedLearningEngine, guided_learning_engine
from graph.builder import create_ekip_planning_graph
from graph.state import EKIPGraphState


@pytest.fixture
def sample_verified_collection():
    """Build synthetic VerifiedKnowledgeCollection for testing."""
    profile = VerificationProfile(
        relevance_score=0.9,
        credibility_score=0.95,
        agreement_score=0.85,
        freshness_score=0.8,
        completeness_score=0.9,
        educational_value_score=0.9,
        overall_score=0.89,
    )
    v1 = VerifiedKnowledgeResult(
        provider="semantic_scholar",
        source_type=SourceType.SEMANTIC_SCHOLAR,
        title="Deep Neural Networks Overview",
        content="Artificial neural networks process complex patterns through layers of interconnected nodes. Backpropagation algorithm: calculates gradients using chain rule.",
        verification_score=0.89,
        profile=profile,
        is_canonical=True,
    )
    v2 = VerifiedKnowledgeResult(
        provider="wikipedia",
        source_type=SourceType.WIKIPEDIA,
        title="Neural Networks Definition",
        content="Neural networks are computing systems inspired by the biological neural networks that constitute animal brains.",
        verification_score=0.82,
        profile=profile,
        is_canonical=False,
    )
    return VerifiedKnowledgeCollection(
        query="Explain Neural Networks",
        verified_results=[v1, v2],
        conflicts=[],
        duplicates=[],
        overall_confidence=0.88,
        overall_agreement=0.90,
        verification_summary="Verified high-confidence academic evidence.",
        ranking=["semantic_scholar", "wikipedia"],
    )


def test_prompt_builder(sample_verified_collection):
    """Verify EducationalPromptBuilder constructs structured grounded prompt."""
    builder = EducationalPromptBuilder()
    prompt = builder.build_synthesis_prompt("Explain Neural Networks", sample_verified_collection)

    assert "Explain Neural Networks" in prompt
    assert "Deep Neural Networks Overview" in prompt
    assert "VERIFIED KNOWLEDGE EVIDENCE" in prompt


def test_knowledge_synthesizer(sample_verified_collection):
    """Verify KnowledgeSynthesizer produces SynthesizedKnowledge with preserved provenance."""
    synthesizer = KnowledgeSynthesizer()
    syn = synthesizer.synthesize(sample_verified_collection)

    assert isinstance(syn, SynthesizedKnowledge)
    assert syn.query == "Explain Neural Networks"
    assert len(syn.primary_explanation) > 0
    assert len(syn.key_takeaways) >= 2
    assert syn.confidence == 0.88
    assert "semantic_scholar" in syn.provenance_map["providers_used"]


def test_response_composer(sample_verified_collection):
    """Verify ResponseComposer creates layered EducationalResponse with citations."""
    synthesizer = KnowledgeSynthesizer()
    composer = ResponseComposer()

    syn = synthesizer.synthesize(sample_verified_collection)
    edu = composer.compose_response(syn, sample_verified_collection)

    assert isinstance(edu, EducationalResponse)
    assert edu.query == "Explain Neural Networks"
    assert len(edu.citations) == 2
    assert len(edu.research) == 1
    assert len(edu.wikipedia) == 1
    assert edu.confidence == 0.88
    assert len(edu.guided_questions) == 3
    assert edu.learning_path is not None


def test_guided_learning_engine():
    """Verify GuidedLearningEngine generates 3 follow-up questions and 4-tier learning path."""
    engine = GuidedLearningEngine()
    qs = engine.generate_guided_questions("Explain Neural Networks")
    path = engine.generate_learning_path("Explain Neural Networks")

    assert len(qs) == 3
    assert "backpropagation" in qs[0].lower() or "gradient" in qs[0].lower()

    assert isinstance(path, LearningPath)
    assert len(path.prerequisites) >= 2
    assert path.current_topic != ""
    assert len(path.next_topics) >= 2
    assert len(path.advanced_topics) >= 2


def test_full_langgraph_11_node_synthesis_pipeline():
    """Verify full 11-node LangGraph execution including planning, collection, verification, ranking, synthesis & guided learning."""
    graph = create_ekip_planning_graph()
    state = graph.invoke({"question": "Explain Neural Networks and Backpropagation"})

    assert isinstance(state, EKIPGraphState)
    assert state.execution_plan is not None

    # Check verified collection container
    assert "verified_collection" in state.provider_metadata or state.verified_collection is not None

    # Check educational response container
    assert "educational_response" in state.provider_metadata or state.educational_response is not None
    edu_dict = state.provider_metadata.get("educational_response") or state.educational_response

    assert edu_dict is not None
    assert "ai_explanation" in edu_dict
    assert "guided_questions" in edu_dict
    assert "learning_path" in edu_dict
    assert len(state.recommended_questions) == 3
