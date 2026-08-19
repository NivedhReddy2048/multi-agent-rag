"""Unit tests for EKIP Step 2G.1 — Targeted Grounding Remediation."""

import pytest
from agents.validation import ValidationAgent
from agents.crag import CRAGAgent
from core.synthesis.prompt_builder import EducationalPromptBuilder
from config.settings import Config


@pytest.fixture
def validation_agent():
    return ValidationAgent()


@pytest.fixture
def crag_agent():
    return CRAGAgent(Config())


# 1. Multi-source claim where Source [1] supports one numeric fact and Source [2] supports another.
def test_remediation_1_multi_source_supporting_both_facts(validation_agent):
    sources = [
        {"content": "EKIP has 8 attention heads.", "source_file": "doc_a.txt"},
        {"content": "EKIP features an embedding dimension of 256.", "source_file": "doc_b.txt"}
    ]
    answer = "EKIP features 8 attention heads and an embedding dimension of 256 [1][2]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "What are EKIP specs?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["faithfulness"] == 1.0
    assert result.metadata["claims_grounded"] == 1
    assert result.metadata["claims_contradicted"] == 0
    assert result.metadata["attribution_valid"] is True


# 2. Multi-source claim containing a genuine contradiction.
def test_remediation_2_multi_source_genuine_contradiction(validation_agent):
    sources = [
        {"content": "EKIP has 8 attention heads.", "source_file": "doc_a.txt"},
        {"content": "EKIP features an embedding dimension of 256.", "source_file": "doc_b.txt"}
    ]
    answer = "EKIP features 14 attention heads and an embedding dimension of 512 [1][2]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "What are EKIP specs?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["claims_contradicted"] == 1
    assert result.metadata["faithfulness"] == 0.0


# 3. Multi-source claim with an invalid citation index.
def test_remediation_3_multi_source_invalid_index(validation_agent):
    sources = [
        {"content": "EKIP has 8 attention heads.", "source_file": "doc_a.txt"},
        {"content": "EKIP features an embedding dimension of 256.", "source_file": "doc_b.txt"}
    ]
    answer = "EKIP features 8 attention heads [1][3]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "What are EKIP specs?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["citations_invalid"] == 1
    assert result.metadata["claims_invalid_citation"] == 1


# 4. Single-source numeric contradiction.
def test_remediation_4_single_source_numeric_contradiction(validation_agent):
    sources = [{"content": "EKIP uses 8 attention heads.", "source_file": "doc_a.txt"}]
    answer = "EKIP uses 12 attention heads [1]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many attention heads?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["claims_contradicted"] == 1
    assert result.metadata["faithfulness"] == 0.0


# 5 & 6. DOCUMENT_ONLY prompt includes strict sentence-level citation instructions & formatting example.
def test_remediation_5_6_document_only_prompt_directives():
    builder = EducationalPromptBuilder()
    from core.planner.execution_plan import ExecutionPlan
    from core.planner.enums import SourceStrategy, EducationalIntent, DifficultyLevel
    from core.models.verification import VerifiedKnowledgeCollection
    plan = ExecutionPlan(
        query="Explain architecture",
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        difficulty=DifficultyLevel.INTERMEDIATE,
        source_strategy=SourceStrategy.DOCUMENT_ONLY
    )
    prompt = builder.build_synthesis_prompt(
        query="Explain architecture",
        verified_collection=VerifiedKnowledgeCollection(verified_results=[]),
        plan=plan,
    )
    assert "SENTENCE-LEVEL CITATION MANDATE" in prompt
    assert "FEW-SHOT CITATION FORMATTING EXAMPLE" in prompt
    assert 'The EKIP-MiniTransformer architecture uses 8 attention heads [1]' in prompt


# 7. GENERAL_KNOWLEDGE prompt behavior remains unaffected.
def test_remediation_7_general_knowledge_prompt_unaffected():
    builder = EducationalPromptBuilder()
    from core.planner.execution_plan import ExecutionPlan
    from core.planner.enums import SourceStrategy, EducationalIntent, DifficultyLevel
    from core.models.verification import VerifiedKnowledgeCollection
    plan = ExecutionPlan(
        query="Explain Transformer attention",
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        difficulty=DifficultyLevel.INTERMEDIATE,
        source_strategy=SourceStrategy.GENERAL_KNOWLEDGE
    )
    prompt = builder.build_synthesis_prompt(
        query="Explain Transformer attention",
        verified_collection=VerifiedKnowledgeCollection(verified_results=[]),
        plan=plan,
    )
    assert "NORMAL EDUCATIONAL MODE & EVIDENCE RELEVANCE PROTOCOL" in prompt
    assert "SENTENCE-LEVEL CITATION MANDATE" not in prompt


# 8. CRAG zero-keyword-overlap case with a sufficiently relevant rerank score.
def test_remediation_8_crag_zero_overlap_relevant_score(crag_agent):
    docs = [{"content": "Unrelated lexical terms for architectural features." * 10, "score": -0.5}]
    is_sufficient, score = crag_agent.evaluate_retrieval("Query", docs, source_strategy="document_only")
    assert is_sufficient is True
    assert score >= 0.35


# 9. CRAG zero-keyword-overlap case with weak/insufficient rerank evidence.
def test_remediation_9_crag_zero_overlap_weak_score(crag_agent):
    docs = [{"content": "Unrelated lexical terms for architectural features.", "score": -5.0}]
    is_sufficient, score = crag_agent.evaluate_retrieval("Query", docs, source_strategy="document_only")
    assert is_sufficient is False
    assert score < 0.35
