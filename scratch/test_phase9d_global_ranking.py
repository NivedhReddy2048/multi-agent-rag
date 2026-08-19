"""
EKIP Phase 9D — Global Evidence Ranking & Citation Determinism Test Suite
Automated offline test suite validating all 9 required Phase 9D test scenarios.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

# Add workspace root to path
sys.path.insert(0, os.path.abspath("."))

from agents.orchestrator import OrchestratorAgent
from core.planner.enums import SourceRole, SourceStrategy, EducationalIntent
from core.planner.execution_plan import ExecutionPlan


class TestPhase9DGlobalRanking(unittest.TestCase):

    def setUp(self):
        self.query = "What is the difference between supervised and unsupervised learning?"

    def test_1_category_insertion_order_bias(self):
        """TEST 1 — High-quality research paper & Wikipedia must outrank low-authority web blogs regardless of insertion order."""
        sources = [
            {
                "title": "Supervised Learning Blog 1",
                "content": "A basic post on supervised learning difference.",
                "source_type": "trusted_web",
                "provider": "tavily",
                "url": "https://random-blog.com/1",
                "score": 0.50,
            },
            {
                "title": "Supervised Learning Blog 2",
                "content": "Another blog post on supervised learning difference.",
                "source_type": "trusted_web",
                "provider": "tavily",
                "url": "https://random-blog.com/2",
                "score": 0.50,
            },
            {
                "title": "Wikipedia: Supervised Learning",
                "content": "Supervised learning is the machine learning task of learning a mapping function.",
                "source_type": "wikipedia",
                "provider": "wikipedia",
                "url": "https://en.wikipedia.org/wiki/Supervised_learning",
                "score": 0.85,
            },
            {
                "title": "Machine Learning Foundations & Supervised Learning",
                "content": "Supervised learning relies on labeled ground-truth targets while unsupervised discovers structure.",
                "source_type": "arxiv",
                "provider": "arxiv",
                "url": "https://arxiv.org/abs/2301.00000",
                "authors": ["Author A"],
                "published_date": "2024-01-01",
                "score": 0.90,
            }
        ]

        ranked = OrchestratorAgent._rank_and_filter_evidence(sources, self.query, intent=EducationalIntent.CONCEPT_EXPLANATION)
        
        # Verify arXiv or Wikipedia is ranked at index 0 (slot [1]), NOT the web blog inserted first
        self.assertTrue(len(ranked) >= 2)
        top_types = [ranked[0].get("source_type"), ranked[1].get("source_type")]
        self.assertIn("arxiv", top_types)
        self.assertIn("wikipedia", top_types)
        self.assertNotEqual(ranked[0].get("source_type"), "trusted_web")
        print("✅ TEST 1 PASSED: Category insertion order bias resolved. Top source is arXiv / Wikipedia.")

    def test_2_concurrent_completion_order_independence(self):
        """TEST 2 — Order A vs Order B input list must produce 100% IDENTICAL final ranked evidence."""
        item1 = {
            "title": "Arxiv Paper",
            "content": "Supervised learning foundational research paper.",
            "source_type": "arxiv",
            "provider": "arxiv",
            "url": "https://arxiv.org/abs/1",
            "score": 0.90,
            "authors": ["A"],
            "published_date": "2024",
        }
        item2 = {
            "title": "Wikipedia Page",
            "content": "Supervised learning wikipedia reference article.",
            "source_type": "wikipedia",
            "provider": "wikipedia",
            "url": "https://en.wikipedia.org/wiki/ML",
            "score": 0.85,
        }
        item3 = {
            "title": "Web Article",
            "content": "Web article explaining machine learning difference.",
            "source_type": "trusted_web",
            "provider": "tavily",
            "url": "https://web.com/article",
            "score": 0.75,
        }

        order_a = [item1, item2, item3]
        order_b = [item3, item1, item2]

        ranked_a = OrchestratorAgent._rank_and_filter_evidence(order_a, self.query)
        ranked_b = OrchestratorAgent._rank_and_filter_evidence(order_b, self.query)

        titles_a = [x.get("title") for x in ranked_a]
        titles_b = [x.get("title") for x in ranked_b]

        self.assertEqual(titles_a, titles_b)
        print("✅ TEST 2 PASSED: Ranking is 100% independent of completion/arrival order.")

    def test_3_official_high_authority_relevance(self):
        """TEST 3 — Official documentation/academic primary sources outrank keyword-stuffed web blogs."""
        blog = {
            "title": "Supervised Learning Unsupervised Learning Machine Learning Difference Comparison",
            "content": "Supervised vs unsupervised learning difference tutorial guide.",
            "source_type": "trusted_web",
            "provider": "tavily",
            "url": "https://seo-blog.com/supervised-learning-unsupervised-learning-difference",
            "score": 0.60,
        }
        official_doc = {
            "title": "Python ML Official Documentation: Supervised & Unsupervised Learning",
            "content": "Official guidelines on supervised and unsupervised learning primitives.",
            "source_type": "internal_document",
            "provider": "uploaded_documents",
            "url": "https://docs.python.org/3/library/ml.html",
            "score": 0.85,
        }

        ranked = OrchestratorAgent._rank_and_filter_evidence([blog, official_doc], self.query)
        self.assertEqual(ranked[0]["title"], official_doc["title"])
        print("✅ TEST 3 PASSED: Official doc outranks keyword-stuffed blog.")

    def test_4_citation_count_bounded_influence(self):
        """TEST 4 — Citation count contributes positively but does not override fresh relevance."""
        old_paper_huge_citations = {
            "title": "Legacy Machine Learning Notes 2005",
            "content": "Historical overview of supervised learning.",
            "source_type": "semantic_scholar",
            "provider": "semantic_scholar",
            "url": "https://semanticscholar.org/paper/old",
            "score": 0.70,
            "citationCount": 10000,
            "published_date": "2005-01-01",
        }
        newer_relevant_paper = {
            "title": "Modern Supervised Learning Architectures",
            "content": "State of the art supervised learning models and unsupervised representation.",
            "source_type": "semantic_scholar",
            "provider": "semantic_scholar",
            "url": "https://semanticscholar.org/paper/new",
            "score": 0.88,
            "citationCount": 100,
            "published_date": "2024-05-01",
        }

        ranked = OrchestratorAgent._rank_and_filter_evidence(
            [old_paper_huge_citations, newer_relevant_paper], self.query
        )
        self.assertEqual(ranked[0]["title"], newer_relevant_paper["title"])
        print("✅ TEST 4 PASSED: Citation count is bounded; high relevance newer paper outranks old paper.")

    def test_5_missing_metadata_safety(self):
        """TEST 5 — Sources missing URL, authors, or dates do not crash and rank deterministically."""
        incomplete_src = {
            "title": "Incomplete Snippet",
            "content": "Supervised learning overview content snippet.",
            "source_type": "trusted_web",
            "provider": "tavily",
        }

        try:
            ranked = OrchestratorAgent._rank_and_filter_evidence([incomplete_src], self.query)
            self.assertEqual(len(ranked), 1)
            self.assertIn("final_score", ranked[0].get("evidence_scores", {}))
            print("✅ TEST 5 PASSED: Safe execution with missing metadata.")
        except Exception as e:
            self.fail(f"Missing metadata caused unexpected crash: {e}")

    def test_6_provider_diversity(self):
        """TEST 6 — Provider diversity preserves representation without inserting low-quality sources."""
        web_items = [
            {
                "title": f"Web Item {i}",
                "content": "Supervised learning content.",
                "source_type": "trusted_web",
                "provider": "tavily",
                "url": f"https://web{i}.com",
                "score": 0.75,
            }
            for i in range(6)
        ]
        wiki_item = {
            "title": "Wikipedia Supervised Learning",
            "content": "Supervised learning article.",
            "source_type": "wikipedia",
            "provider": "wikipedia",
            "url": "https://en.wikipedia.org/wiki/SL",
            "score": 0.85,
        }
        arxiv_item = {
            "title": "ArXiv Supervised Learning Research",
            "content": "Supervised learning research paper.",
            "source_type": "arxiv",
            "provider": "arxiv",
            "url": "https://arxiv.org/abs/999",
            "score": 0.90,
            "authors": ["Author Z"],
            "published_date": "2024",
        }

        all_sources = web_items + [wiki_item, arxiv_item]
        ranked = OrchestratorAgent._rank_and_filter_evidence(all_sources, self.query)

        # Check diversity in top 6
        provs = [x.get("provider") for x in ranked[:6]]
        self.assertIn("arxiv", provs)
        self.assertIn("wikipedia", provs)
        self.assertIn("tavily", provs)
        print("✅ TEST 6 PASSED: Provider diversity preserved across top factual evidence slots.")

    def test_7_learning_resource_isolation(self):
        """TEST 7 — Learning resources (YouTube, GitHub) never consume factual evidence slots."""
        yt_items = [
            {
                "title": f"Video Tutorial {i}",
                "content": "Watch video on supervised learning.",
                "source_type": "youtube",
                "provider": "youtube",
                "url": f"https://youtube.com/watch?v={i}",
                "score": 0.90,
            }
            for i in range(10)
        ]
        gh_items = [
            {
                "title": f"GitHub Repo {i}",
                "content": "Code repo for supervised learning.",
                "source_type": "github_repo",
                "provider": "github",
                "url": f"https://github.com/user/repo{i}",
                "score": 0.90,
            }
            for i in range(10)
        ]
        factual_items = [
            {
                "title": f"Factual Doc {i}",
                "content": "Factual text chunk on supervised learning.",
                "source_type": "internal_document",
                "provider": "uploaded_documents",
                "url": f"doc_{i}.pdf",
                "score": 0.85,
            }
            for i in range(3)
        ]

        all_sources = yt_items + gh_items + factual_items
        ranked = OrchestratorAgent._rank_and_filter_evidence(all_sources, self.query)

        # Factual evidence must appear first in list
        factual_result = [x for x in ranked if x.get("source_role") == SourceRole.FACTUAL_EVIDENCE.value]
        learning_result = [x for x in ranked if x.get("source_role") == SourceRole.LEARNING_RESOURCE.value]

        self.assertEqual(len(factual_result), 3)
        self.assertTrue(len(learning_result) > 0)
        # Factual results must precede learning results in list returned to SynthesisAgent
        first_learning_idx = next(idx for idx, x in enumerate(ranked) if x.get("source_role") == SourceRole.LEARNING_RESOURCE.value)
        self.assertGreaterEqual(first_learning_idx, 3)
        print("✅ TEST 7 PASSED: Learning resources strictly isolated from factual slots.")

    def test_8_strict_document_only_regression(self):
        """TEST 8 — Strict DOCUMENT_ONLY policy with 0 docs returns INSUFFICIENT_EVIDENCE fallback."""
        from agents.orchestrator import OrchestratorAgent
        from config.settings import Config
        cfg = Config()
        engine = MagicMock()
        memory = MagicMock()
        orch = OrchestratorAgent(cfg, engine, memory)
        orch.retrieval = MagicMock()
        orch.retrieval.run.return_value = MagicMock(sources=[], confidence=0.0)

        plan = ExecutionPlan(
            query="Strict doc query",
            intent=EducationalIntent.DOCUMENT_QUERY,
            source_strategy=SourceStrategy.DOCUMENT_ONLY
        )
        context = {
            "query": "Strict doc query",
            "execution_plan": plan,
            "source_strategy": "document_only"
        }

        res = orch.run(context)
        self.assertEqual(res.metadata.get("response_status"), "INSUFFICIENT_EVIDENCE")
        self.assertEqual(len(res.sources), 0)
        print("✅ TEST 8 PASSED: Strict DOCUMENT_ONLY returns INSUFFICIENT_EVIDENCE when 0 docs found.")

    def test_9_citation_determinism(self):
        """TEST 9 — Repeated execution with fixed factual set produces identical citation indexing."""
        import copy
        sources_a = [
            {
                "title": "Doc A",
                "content": "Content A",
                "source_type": "internal_document",
                "provider": "uploaded_documents",
                "url": "https://docs.python.org/doc_a.html",
                "score": 0.90,
            },
            {
                "title": "Doc B",
                "content": "Content B",
                "source_type": "wikipedia",
                "provider": "wikipedia",
                "url": "https://wikipedia.org/b",
                "score": 0.85,
            },
            {
                "title": "Doc C",
                "content": "Content C",
                "source_type": "arxiv",
                "provider": "arxiv",
                "url": "https://arxiv.org/c",
                "score": 0.80,
            }
        ]
        sources_b = copy.deepcopy(sources_a)

        run1 = OrchestratorAgent._rank_and_filter_evidence(sources_a, self.query)
        run2 = OrchestratorAgent._rank_and_filter_evidence(sources_b, self.query)

        self.assertEqual([x["title"] for x in run1], [x["title"] for x in run2])
        self.assertEqual(run1[0]["title"], "Doc A")
        self.assertEqual(run1[1]["title"], "Doc C")
        self.assertEqual(run1[2]["title"], "Doc B")
        print("✅ TEST 9 PASSED: Citation order mapping is 100% deterministic.")


if __name__ == "__main__":
    unittest.main()
