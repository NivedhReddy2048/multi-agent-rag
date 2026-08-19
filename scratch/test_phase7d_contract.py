"""Phase 7D Contract & Link Integrity Verification Test Suite."""

import sys
from core.models.domain import KnowledgeResult, SourceType
from agents.orchestrator import OrchestratorAgent
from core.synthesis.agent_response_adapter import agent_response_adapter


def run_tests():
    print("=" * 70)
    print("RUNNING EKIP PHASE 7D CONTRACT & LINK INTEGRITY TEST SUITE")
    print("=" * 70)

    # 1. Test YouTube KnowledgeResult Normalization
    yt_kr = KnowledgeResult(
        provider="youtube",
        source_type=SourceType.VIDEO,
        title="Video: Docker Crash Course for Beginners",
        content="Learn Docker fundamentals in 45 minutes.",
        url="https://www.youtube.com/watch?v=12345",
        authors=["tech_with_tim"],
        metadata={"channel": "Tech With Tim", "video_url": "https://www.youtube.com/watch?v=12345"}
    )

    orch = OrchestratorAgent.__new__(OrchestratorAgent)
    norm_yt = orch._normalize_knowledge_result(yt_kr)

    print("\n[Test 1] YouTube Normalization:")
    print(f"  Title: {norm_yt.get('title')}")
    print(f"  URL: {norm_yt.get('url')}")
    print(f"  Channel: {norm_yt.get('channel_name')}")
    assert norm_yt["url"] == "https://www.youtube.com/watch?v=12345", "YouTube URL must be preserved"
    assert norm_yt["channel_name"] == "Tech With Tim", "YouTube Channel Name must be preserved"
    print("  ✅ TEST 1 PASSED: YouTube metadata preserved.")

    # 2. Test GitHub KnowledgeResult Normalization
    gh_kr = KnowledgeResult(
        provider="github",
        source_type=SourceType.GITHUB_REPO,
        title="tiangolo/fastapi",
        content="FastAPI framework, high performance, easy to learn, fast to code, ready for production",
        url="https://github.com/tiangolo/fastapi",
        authors=["tiangolo"],
        metadata={"stars": 75000, "full_name": "tiangolo/fastapi"}
    )

    norm_gh = orch._normalize_knowledge_result(gh_kr)

    print("\n[Test 2] GitHub Normalization:")
    print(f"  Title: {norm_gh.get('title')}")
    print(f"  URL: {norm_gh.get('url')}")
    print(f"  Stars: {norm_gh.get('star_count')}")
    assert norm_gh["url"] == "https://github.com/tiangolo/fastapi", "GitHub URL must be preserved"
    assert norm_gh["star_count"] == 75000, "GitHub star count must be preserved"
    print("  ✅ TEST 2 PASSED: GitHub repository metadata preserved.")

    # 3. Test Deduplication Strategy
    sources = [
        {"title": "FastAPI Repo", "url": "https://github.com/tiangolo/fastapi", "provider": "github"},
        {"title": "FastAPI Repo", "url": "https://github.com/tiangolo/fastapi", "provider": "github"},  # Exact duplicate
        {"title": "FastAPI Repo", "url": "https://github.com/tiangolo/fastapi-mirror", "provider": "github"},  # Duplicate title & provider
        {"title": "Docker Video", "url": "https://youtube.com/watch?v=1", "provider": "youtube"},
    ]
    deduped = orch._deduplicate_sources(sources)
    print(f"\n[Test 3] Deduplication: Original {len(sources)} -> Deduped {len(deduped)}")
    assert len(deduped) == 2, f"Expected 2 unique sources, got {len(deduped)}"
    print("  ✅ TEST 3 PASSED: Deduplication eliminates duplicate URLs and provider:title collisions.")

    # 4. Test Adapter Categorization
    class DummyAgentResult:
        content = "Here are resources for learning FastAPI and Docker."
        confidence = 85
        sources = [norm_yt, norm_gh]
        metadata = {"response_status": "SUCCESS"}
        success = True
        error = None

    res = agent_response_adapter.compose_from_agent_result(DummyAgentResult())

    print("\n[Test 4] Adapter Categorization:")
    print(f"  Videos count: {len(res.get('videos', []))}")
    print(f"  Code examples count: {len(res.get('code_examples', []))}")
    assert len(res.get("videos", [])) == 1, "Video resource must be in videos bucket"
    assert len(res.get("code_examples", [])) == 1, "GitHub resource must be in code_examples bucket"
    assert res["videos"][0]["url"] == "https://www.youtube.com/watch?v=12345"
    assert res["code_examples"][0]["url"] == "https://github.com/tiangolo/fastapi"
    print("  ✅ TEST 4 PASSED: Adapter categorized resources without metadata loss.")

    print("\n" + "=" * 70)
    print("ALL PHASE 7D CONTRACT TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
