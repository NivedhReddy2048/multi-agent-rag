"""YouTube Knowledge Agent for Educational Video Lecture Recommendations."""

import time
from typing import List
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.providers import provider_registry
from core.logger import get_logger

logger = get_logger("agents.sources.youtube_agent")


class YoutubeKnowledgeAgent(BaseKnowledgeAgent):
    """Retrieves educational videos and video lecture metadata from YouTube Data API v3."""

    def __init__(self):
        super().__init__(
            agent_name="YoutubeKnowledgeAgent",
            source_type=SourceType.VIDEO,
            provider_key="youtube"
        )

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health(self) -> bool:
        p = provider_registry.get_provider("youtube")
        return p is not None

    def execute(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        t0 = time.time()
        results: List[KnowledgeResult] = []

        p = provider_registry.get_provider("youtube")
        if p:
            try:
                res = p.search(query, max_results=max_results)
                lat = (time.time() - t0) * 1000
                if res.success and res.data:
                    raw_items = res.data if isinstance(res.data, list) else res.data.get("videos", res.data.get("items", []))
                    for item in raw_items:
                        title = item.get("title", "Educational Video")
                        desc = item.get("description", item.get("snippet", ""))
                        v_url = item.get("video_url", item.get("url", f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId', '')}"))
                        channel = item.get("channel", item.get("channelTitle", ""))

                        if v_url and v_url != "https://www.youtube.com/watch?v=":
                            results.append(KnowledgeResult(
                                provider="youtube",
                                source_type=SourceType.VIDEO,
                                title=f"Video: {title}" if not title.startswith("Video:") else title,
                                content=desc or f"Educational video tutorial by {channel}.",
                                summary=desc[:200] + "..." if len(desc) > 200 else desc,
                                url=v_url,
                                authors=[channel] if channel else [],
                                confidence=0.85,
                                latency_ms=lat,
                                metadata={"channel": channel, "video_url": v_url},
                            ))
                    logger.info(f"YoutubeKnowledgeAgent retrieved {len(results)} videos via YouTube API in {int(lat)}ms")
            except Exception as e:
                logger.error(f"YoutubeKnowledgeAgent API error: {e}", exc_info=True)

        # Fallback to web search for YouTube/video URLs if direct API returned 0 items
        if not results:
            logger.info("YoutubeKnowledgeAgent: Direct YouTube API yielded 0 items; executing web video search fallback.")
            try:
                from core.providers.trusted_web import trusted_web_provider_manager
                web_res = trusted_web_provider_manager.search(f"{query} video site:youtube.com", max_results=max_results)
                if not web_res or not web_res.success or not web_res.data:
                    web_res = trusted_web_provider_manager.search(f"{query} video tutorial", max_results=max_results)
                if web_res and web_res.success and web_res.data:
                    raw_items = web_res.data if isinstance(web_res.data, list) else web_res.data.get("results", [])
                    for item in raw_items:
                        v_url = item.get("url", item.get("link", item.get("href", "")))
                        title = item.get("title", "Educational Video")
                        content = item.get("content", item.get("snippet", item.get("body", "")))
                        if v_url and (
                            "youtube.com" in v_url.lower() or
                            "youtu.be" in v_url.lower() or
                            "vimeo.com" in v_url.lower() or
                            "video" in title.lower() or
                            "video" in query.lower()
                        ):
                            clean_title = f"Video: {title}" if not title.startswith("Video:") else title
                            results.append(KnowledgeResult(
                                provider="youtube",
                                source_type=SourceType.VIDEO,
                                title=clean_title,
                                content=content or f"Educational video for {query}",
                                summary=content[:200] if content else f"Educational video resource: {title}",
                                url=v_url,
                                authors=["YouTube Web"],
                                confidence=0.80,
                                latency_ms=(time.time() - t0) * 1000,
                                metadata={"channel": "YouTube Web", "video_url": v_url},
                            ))
                    logger.info(f"YoutubeKnowledgeAgent retrieved {len(results)} videos via web fallback")
            except Exception as fallback_err:
                logger.warning(f"YoutubeKnowledgeAgent web fallback error: {fallback_err}")

        return results
