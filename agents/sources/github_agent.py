"""GitHub Knowledge Agent for Open-Source Repositories and Code Examples."""

import re
import time
from typing import List
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.providers import provider_registry
from core.logger import get_logger

logger = get_logger("agents.sources.github_agent")


class GithubKnowledgeAgent(BaseKnowledgeAgent):
    """Retrieves open-source code repositories and implementation examples from GitHub REST API v3 and Tavily fallback."""

    def __init__(self):
        super().__init__(
            agent_name="GithubKnowledgeAgent",
            source_type=SourceType.GITHUB_REPO,
            provider_key="github"
        )

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health(self) -> bool:
        p = provider_registry.get_provider("github")
        return p is not None

    def _build_github_search_query(self, user_query: str) -> str:
        """Extract core technical topic from conversational user prompt deterministically."""
        q = user_query.strip()
        phrases_to_remove = [
            r"\bi want to learn\b",
            r"\bi want\b",
            r"\brecommend useful\b",
            r"\brecommend\b",
            r"\bgive me\b",
            r"\bshow me\b",
            r"\bfrom beginner to advanced\b",
            r"\bbeginner to advanced\b",
            r"\bfor learning\b",
            r"\blearning explanation\b",
            r"\bopen source projects?\b",
            r"\bopen-source projects?\b",
            r"\bopen source repositories\b",
            r"\bopen source repos\b",
            r"\bgithub repositories\b",
            r"\bgithub repository\b",
            r"\bgithub repos?\b",
            r"\bgithub\b",
            r"\brepositories\b",
            r"\brepository\b",
            r"\brepos?\b",
            r"\bprojects?\b",
            r"\bcodebases?\b",
            r"\buseful\b",
            r"\bbest\b",
            r"\blearning\b",
            r"\bexplanation\b",
            r"\brelated to\b",
            r"\bto learn\b",
            r"\bplease\b",
            r"\byoutube videos?\b",
            r"\bvideos?\b",
            r"\brecommendation\b",
            r"\baccording to\b",
            r"\bexplain\b",
            r"\bbriefly\b",
            r"\bin detail\b",
            r"\bdetailed\b",
            r"\bconcepts?\b",
            r"\bguide\b",
            r"\btutorial\b",
            r"\bhow to\b",
            r"\band\b",
            r"\ba\b",
            r"\bthe\b",
            r"\bor\b",
            r"\bof\b",
            r"\bto\b",
            r"\bin\b",
            r"\bon\b",
            r"\bfor\b",
            r"\bwith\b",
            r"\bfrom\b",
            r"\bit\b",
            r"\bme\b",
            r"\bi\b",
        ]
        cleaned = q
        for pattern in phrases_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Clean up punctuation and multiple spaces
        cleaned = re.sub(r"[\.,!\?\;\:]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned if len(cleaned) >= 2 else user_query.strip()

    def execute(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        t0 = time.time()
        results: List[KnowledgeResult] = []
        seen_urls = set()

        clean_topic = self._build_github_search_query(query)
        logger.info(f"GithubKnowledgeAgent normalized query: '{query}' -> '{clean_topic}'")

        # 1. Primary Attempt: GitHub REST API v3
        p_github = provider_registry.get_provider("github")
        if p_github:
            try:
                res = p_github.search(clean_topic, max_results=max_results)
                lat = (time.time() - t0) * 1000
                if res.success and res.data:
                    raw_items = res.data if isinstance(res.data, list) else res.data.get("items", [])
                    for repo in raw_items:
                        full_name = repo.get("full_name", repo.get("name", "GitHub Repo"))
                        desc = repo.get("description", repo.get("snippet", "Open source GitHub repository.")) or "No description."
                        url = repo.get("html_url", repo.get("url", "")).strip().rstrip("/")
                        stars = repo.get("stargazers_count", 0)
                        lang = repo.get("language", "Code")

                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            results.append(KnowledgeResult(
                                provider="github",
                                source_type=SourceType.GITHUB_REPO,
                                title=f"GitHub: {full_name}",
                                content=f"{desc} (Stars: {stars}, Language: {lang})",
                                summary=desc[:200] + "..." if len(desc) > 200 else desc,
                                url=url,
                                confidence=0.85,
                                latency_ms=lat,
                                metadata={"stars": stars, "language": lang, "full_name": full_name},
                            ))
                    logger.info(f"GithubKnowledgeAgent API retrieved {len(results)} repos in {int(lat)}ms")
                else:
                    logger.warning(f"GithubKnowledgeAgent API returned 0 results or failed: {res.error}")
            except Exception as e:
                logger.error(f"GithubKnowledgeAgent API error: {e}", exc_info=True)

        # 2. Secondary Fallback: Tavily Web Search for site:github.com
        if len(results) < max_results:
            try:
                p_tavily = provider_registry.get_provider("tavily")
                if p_tavily:
                    t_tav = time.time()
                    tav_query = f"site:github.com {clean_topic}"
                    tav_res = p_tavily.search(tav_query, max_results=max_results * 2)
                    lat_tav = (time.time() - t_tav) * 1000
                    if tav_res.success and tav_res.data:
                        items = tav_res.data if isinstance(tav_res.data, list) else tav_res.data.get("results", [])
                        for item in items:
                            raw_url = item.get("url", "").strip()
                            repo_match = re.match(
                                r"^https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:/.*)?$",
                                raw_url
                            )
                            if repo_match:
                                owner, repo_name = repo_match.group(1), repo_match.group(2)
                                if owner.lower() in ("features", "topics", "pricing", "about", "security", "enterprise", "customer-stories", "readme", "orgs", "settings", "site"):
                                    continue
                                canonical_url = f"https://github.com/{owner}/{repo_name}"
                                if canonical_url in seen_urls:
                                    continue
                                seen_urls.add(canonical_url)

                                snippet = item.get("content", item.get("snippet", "GitHub repository resource.")) or "No description."

                                results.append(KnowledgeResult(
                                    provider="github",
                                    source_type=SourceType.GITHUB_REPO,
                                    title=f"GitHub: {owner}/{repo_name}",
                                    content=snippet,
                                    summary=snippet[:200] + "..." if len(snippet) > 200 else snippet,
                                    url=canonical_url,
                                    confidence=0.80,
                                    latency_ms=lat_tav,
                                    metadata={"stars": None, "language": "Repository", "full_name": f"{owner}/{repo_name}"},
                                ))
                                if len(results) >= max_results:
                                    break
                        logger.info(f"GithubKnowledgeAgent Tavily fallback retrieved {len(results)} total repos")
            except Exception as err:
                logger.error(f"GithubKnowledgeAgent Tavily fallback error: {err}", exc_info=True)

        return results

