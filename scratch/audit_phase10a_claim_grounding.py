"""
EKIP Phase 10A — Claim-Level Grounding & Citation Entailment Audit Script
Audits ValidationAgent's handling of 12 controlled entailment test scenarios and runtime queries.
STRICT READ-ONLY: Does not modify any production code.
"""

import os
import sys
import unittest

# Add workspace root to path
sys.path.insert(0, os.path.abspath("."))

from config.settings import Config
from agents.validation import ValidationAgent
from core.planner.enums import SourceRole, SourceStrategy, EducationalIntent


from core.validation.entailment_evaluator import EntailmentEvaluator

def run_phase10a_entailment_audit():
    print("=" * 60, flush=True)
    print("EKIP PHASE 10A — CLAIM-LEVEL GROUNDING & ENTAILMENT AUDIT", flush=True)
    print("=" * 60, flush=True)

    validator = ValidationAgent(evaluator=EntailmentEvaluator(disabled=True))

    test_cases = [
        {
            "id": "TEST 1",
            "name": "Correct Claim + Correct Citation",
            "answer": "Python was created by Guido van Rossum [1].",
            "sources": [
                {"title": "Python Overview", "content": "Python is a programming language created by Guido van Rossum in 1991.", "provider": "uploaded_documents"}
            ],
            "expected_verdict": "SUPPORTED"
        },
        {
            "id": "TEST 2",
            "name": "Correct Claim + Wrong Citation",
            "answer": "Python was created by Guido van Rossum [1].",
            "sources": [
                {"title": "Java Documentation", "content": "Java is an object-oriented language created by James Gosling at Sun Microsystems.", "provider": "uploaded_documents"}
            ],
            "expected_verdict": "UNSUPPORTED (SEMANTIC_MISMATCH)"
        },
        {
            "id": "TEST 3",
            "name": "Citation Exists But Does Not Support Specific Detail",
            "answer": "The Transformer model uses exactly 12 attention heads [1].",
            "sources": [
                {"title": "Attention Paper", "content": "The Transformer architecture relies on multi-head self-attention mechanisms.", "provider": "arxiv"}
            ],
            "expected_verdict": "UNSUPPORTED (Detail Not Found)"
        },
        {
            "id": "TEST 4",
            "name": "Unsupported Hallucinated Claim",
            "answer": "Transformer training always requires billions of parameters.",
            "sources": [
                {"title": "Attention Paper", "content": "The Transformer model achieves state of the art results in translation.", "provider": "arxiv"}
            ],
            "expected_verdict": "UNSUPPORTED"
        },
        {
            "id": "TEST 5",
            "name": "Multi-Source Claim",
            "answer": "BERT uses Transformer encoders [1] and is pre-trained with masked language modeling [2].",
            "sources": [
                {"title": "Transformer Paper", "content": "The Transformer architecture is based entirely on self-attention encoders.", "provider": "arxiv"},
                {"title": "BERT Paper", "content": "BERT is pre-trained using a masked language modeling objective.", "provider": "arxiv"}
            ],
            "expected_verdict": "SUPPORTED"
        },
        {
            "id": "TEST 6",
            "name": "Conflicting Sources",
            "answer": "The system architecture uses 12 layers [1].",
            "sources": [
                {"title": "Doc A", "content": "The system architecture uses 12 layers.", "provider": "uploaded_documents"},
                {"title": "Doc B", "content": "The system architecture uses 24 layers.", "provider": "uploaded_documents"}
            ],
            "expected_verdict": "SUPPORTED (with conflict detected at synthesis stage)"
        },
        {
            "id": "TEST 7",
            "name": "Citation Index Valid But Semantically Wrong",
            "answer": "Supervised learning requires labeled training data [2].",
            "sources": [
                {"title": "Supervised ML", "content": "Supervised learning maps inputs to target outputs using labeled data.", "provider": "wikipedia"},
                {"title": "Unrelated Recipe", "content": "Preheat oven to 350 degrees Fahrenheit and bake for 20 minutes.", "provider": "trusted_web"}
            ],
            "expected_verdict": "SEMANTIC_MISMATCH (Index 2 valid but wrong content)"
        },
        {
            "id": "TEST 8",
            "name": "General Knowledge Explanation",
            "answer": "Think of attention as a mechanism that helps the model focus on relevant information.",
            "sources": [],
            "source_strategy": "general_knowledge",
            "source_mode": "general_knowledge",
            "expected_verdict": "GENERAL_EXPLANATION"
        },
        {
            "id": "TEST 9",
            "name": "Numeric Claim",
            "answer": "The embedding dimension is 768 [1].",
            "sources": [
                {"title": "BERT Spec", "content": "The standard base model embedding dimension is 768.", "provider": "uploaded_documents"}
            ],
            "expected_verdict": "SUPPORTED"
        },
        {
            "id": "TEST 10",
            "name": "Citation Attached To Entire Paragraph",
            "answer": "Transformers were introduced in 2017. They use multi-head attention. They eliminate recurrence. They achieve high BLEU scores. They require 8 GPUs [1].",
            "sources": [
                {"title": "Attention Paper", "content": "We propose the Transformer in 2017, using multi-head attention and eliminating recurrence.", "provider": "arxiv"}
            ],
            "expected_verdict": "PARTIALLY_SUPPORTED (Trailing details uncited/unsupported)"
        },
        {
            "id": "TEST 11",
            "name": "Research Paper Attribution",
            "answer": "Vaswani et al. introduced the Transformer architecture in 2017 [1].",
            "sources": [
                {"title": "Attention Is All You Need", "content": "Vaswani, Shazeer, Parmar et al. introduced the Transformer architecture in 2017.", "provider": "arxiv", "authors": ["Vaswani"], "published_date": "2017"}
            ],
            "expected_verdict": "SUPPORTED"
        },
        {
            "id": "TEST 12",
            "name": "Contradicted Claim",
            "answer": "The model accuracy reached 92% [1].",
            "sources": [
                {"title": "Experiment Log", "content": "The final model accuracy was 82% on the test set.", "provider": "uploaded_documents"}
            ],
            "expected_verdict": "CONTRADICTED"
        }
    ]

    print("\n" + "-" * 60, flush=True)
    print("EXECUTING 12 CONTROLLED ENTAILMENT SCENARIOS AGAINST ValidationAgent", flush=True)
    print("-" * 60, flush=True)

    results = []
    for tc in test_cases:
        ctx = {
            "query": "Audit Query",
            "answer": tc["answer"],
            "sources": tc.get("sources", []),
            "source_mode": tc.get("source_mode", "documents" if tc.get("sources") else "none"),
            "source_strategy": tc.get("source_strategy", "document_augmented" if tc.get("sources") else "general_knowledge")
        }
        res = validator.run(ctx)
        meta = res.metadata
        
        # Analyze claim level detail
        extracted = validator._extract_claims_and_structure(tc["answer"])
        claims_eval = []
        for c in extracted:
            verdict = validator._evaluate_claim_against_sources(c, tc.get("sources", []))
            claims_eval.append((c["text"], c["citations"], verdict))

        results.append({
            "id": tc["id"],
            "name": tc["name"],
            "expected": tc["expected_verdict"],
            "faithfulness": meta.get("faithfulness"),
            "warnings": meta.get("warnings", []),
            "claims_eval": claims_eval
        })

        print(f"\n[{tc['id']}] {tc['name']}:", flush=True)
        print(f"  Answer: \"{tc['answer']}\"", flush=True)
        print(f"  Validation Faithfulness: {meta.get('faithfulness')} | Warnings: {meta.get('warnings')}", flush=True)
        for text, cids, v in claims_eval:
            print(f"    Claim: \"{text}\" | Citations: {cids} | Validation Verdict: {v}", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("PHASE 10A DIAGNOSTIC AUDIT COMPLETE", flush=True)
    print("=" * 60, flush=True)

if __name__ == "__main__":
    run_phase10a_entailment_audit()
