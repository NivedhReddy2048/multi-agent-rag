"""Tests for Step 2F — Deterministic Citation Verification & Claim-Level Grounding in EKIP Platform."""

import pytest
from agents.validation import ValidationAgent

class DummyConfig:
    pass

@pytest.fixture
def validation_agent():
    return ValidationAgent()


def test_scenario_1_correct_citation_supported_claim(validation_agent):
    sources = [{"content": "The EKIP model contains 8 attention heads.", "source_file": "doc_a.txt"}]
    answer = "The EKIP model contains 8 attention heads [1]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many attention heads does EKIP contain?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.success is True
    assert result.metadata["faithfulness"] == 1.0
    assert result.metadata["claims_grounded"] == 1
    assert result.metadata["citations_valid"] == 1
    assert result.metadata["citations_invalid"] == 0
    assert result.metadata["attribution_valid"] is True


def test_scenario_2_citation_with_unsupported_claim(validation_agent):
    sources = [{"content": "The EKIP model contains 8 attention heads.", "source_file": "doc_a.txt"}]
    answer = "The EKIP model features quantum annealing processors [1]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "Does EKIP feature quantum annealing?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["faithfulness"] == 0.0
    assert result.metadata["claims_unsupported"] == 1
    assert result.metadata["attribution_valid"] is False


def test_scenario_3_numeric_contradiction(validation_agent):
    sources = [{"content": "The architecture uses 8 attention heads.", "source_file": "doc_a.txt"}]
    answer = "The architecture uses 12 attention heads [1]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many attention heads?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["faithfulness"] == 0.0
    assert result.metadata["claims_contradicted"] == 1
    assert "EVIDENCE_CONTRADICTION_DETECTED" in result.metadata["warnings"]
    assert result.metadata["attribution_valid"] is False


def test_scenario_4_out_of_range_citation_high(validation_agent):
    sources = [
        {"content": "Source 1 content", "source_file": "doc_a.txt"},
        {"content": "Source 2 content", "source_file": "doc_b.txt"}
    ]
    answer = "The model uses positional encoding [3]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "Positional encoding?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["citations_invalid"] == 1
    assert result.metadata["claims_invalid_citation"] == 1
    assert "INVALID_CITATION_INDEX_DETECTED" in result.metadata["warnings"]


def test_scenario_5_out_of_range_citation_zero(validation_agent):
    sources = [{"content": "Source 1 content", "source_file": "doc_a.txt"}]
    answer = "The model uses positional encoding [0]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "Positional encoding?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["citations_invalid"] == 1
    assert result.metadata["claims_invalid_citation"] == 1
    assert "INVALID_CITATION_INDEX_DETECTED" in result.metadata["warnings"]


def test_scenario_6_misattribution(validation_agent):
    sources = [
        {"content": "EKIP uses 8 attention heads.", "source_file": "doc_a.txt"},
        {"content": "EKIP encoder contains 6 layers.", "source_file": "doc_b.txt"}
    ]
    # Encoder 6 layers is in Source 2, but cited as [1]
    answer = "The encoder contains 6 layers [1]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many layers in encoder?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["claims_unsupported"] == 1
    assert result.metadata["attribution_valid"] is False


def test_scenario_7_multiple_citations_both_support(validation_agent):
    sources = [
        {"content": "EKIP model employs multi-head self-attention mechanism.", "source_file": "doc_a.txt"},
        {"content": "EKIP model utilizes self-attention blocks.", "source_file": "doc_b.txt"}
    ]
    answer = "The EKIP model employs self-attention blocks [1][2]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "What mechanism does EKIP use?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["faithfulness"] == 1.0
    assert result.metadata["claims_grounded"] == 1
    assert result.metadata["citations_valid"] == 2


def test_scenario_8_multiple_citations_one_contradicts(validation_agent):
    sources = [
        {"content": "EKIP model uses 8 attention heads.", "source_file": "doc_a.txt"},
        {"content": "EKIP model uses 12 attention heads.", "source_file": "doc_b.txt"}
    ]
    answer = "The EKIP model uses 8 attention heads [1][2]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many attention heads?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["claims_contradicted"] == 1
    assert result.metadata["faithfulness"] == 0.0


def test_scenario_9_markdown_heading_pollution_excluded(validation_agent):
    sources = [{"content": "EKIP-MiniTransformer employs 8 attention heads.", "source_file": "doc_a.txt"}]
    answer = """### 1. Problem & Motivation
In deep learning, transformers require self-attention mechanisms.

### 2. Core Architecture
EKIP-MiniTransformer employs 8 attention heads [1].

### 3. Conclusion
This concludes the overview.
"""
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many attention heads does EKIP-MiniTransformer employ?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    # Headings and conclusion structural lines should NOT pollute the denominator
    assert result.metadata["faithfulness"] == 1.0
    assert result.metadata["claims_grounded"] == 1


def test_scenario_10_code_blocks_excluded_from_claims(validation_agent):
    sources = [{"content": "EKIP encoder contains 6 blocks.", "source_file": "doc_a.txt"}]
    answer = """The EKIP encoder contains 6 blocks [1].

```python
def forward(x):
    return self.encoder(x)
```
"""
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many blocks?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["claims_grounded"] == 1
    assert result.metadata["claims_applicable"] == 1
    assert result.metadata["faithfulness"] == 1.0


def test_scenario_11_missing_evidence_disclaimers_faithful(validation_agent):
    sources = [{"content": "EKIP encoder details.", "source_file": "doc_a.txt"}]
    answer = "I couldn't find relevant information about your query in doc_a.txt."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "Explain decoder specs",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["faithfulness"] == 1.0
    assert result.metadata["claims_grounded"] == 1


def test_scenario_12_general_knowledge_not_applicable(validation_agent):
    sources = []
    answer = "Transformer architecture uses multi-head self-attention."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "Explain transformer architecture",
        "source_mode": "general_knowledge",
        "source_strategy": "general_knowledge"
    })
    assert result.metadata["faithfulness"] is None
    assert result.metadata["faithfulness_applicable"] is False
    assert result.metadata["faithfulness_reason"] == "general_knowledge_no_document_grounding_required"


def test_scenario_13_step2e_grounded_citation_survival(validation_agent):
    sources = [{"content": "EKIP-Alpha states that it uses 8 attention heads.", "source_file": "doc_a.txt"}]
    answer = "EKIP-Alpha states that it uses 8 attention heads [1]."
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many attention heads?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    assert result.metadata["faithfulness"] == 1.0
    assert result.metadata["citations_valid"] == 1


def test_scenario_14_no_artificial_dilution(validation_agent):
    sources = [{"content": "EKIP-MiniTransformer employs 8 attention heads.", "source_file": "doc_a.txt"}]
    answer = """## Overview
EKIP-MiniTransformer employs 8 attention heads in its multi-head self-attention layers [1].
"""
    result = validation_agent.run({
        "answer": answer,
        "sources": sources,
        "query": "How many attention heads?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    # Previously produced ~0.08 due to denominator dilution. Now must produce 1.0!
    assert result.metadata["faithfulness"] == 1.0
