"""YouTube Data API Provider Wrapper for Educational Videos."""

import time
import requests
from typing import List, Dict, Any
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class YoutubeProvider(BaseProvider):
    """YouTube Data API v3 Educational Video Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="youtube", category=ProviderCategory.VIDEO, is_optional=True)
        self.api_key = Config.YOUTUBE_DATA_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3/search"

    def initialize(self) -> bool:
        if not self.api_key:
            self.last_error = "YOUTUBE_DATA_API_KEY is missing."
            self.is_initialized = False
            return False
        self.is_initialized = True
        return True

    def health_check(self) -> ProviderResponse:
        t0 = time.time()
        if not self.initialize():
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.NOT_CONFIGURED.value,
                error=self.last_error,
                metadata={"api_key_masked": mask_api_key(self.api_key)},
            )
        latency = round((time.time() - t0) * 1000, 2)
        return ProviderResponse(
            success=True,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.READY.value,
            latency_ms=latency,
            data={"configured": True, "engine": "YouTube Data API v3"},
            metadata={"api_key_masked": mask_api_key(self.api_key)},
        )

    def search(self, query: str, max_results: int = 5, **kwargs) -> ProviderResponse:
        t0 = time.time()
        if not self.is_initialized and not self.initialize():
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.NOT_CONFIGURED.value,
                error="YouTube Data API key missing.",
            )

        # 1. Try googleapiclient SDK if available
        try:
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", developerKey=self.api_key)
            req = youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=max_results,
                safeSearch="moderate"
            )
            res = req.execute()
            items = res.get("items", [])
            parsed = [
                {
                    "title": item.get("snippet", {}).get("title", ""),
                    "channel": item.get("snippet", {}).get("channelTitle", ""),
                    "published_at": item.get("snippet", {}).get("publishedAt", ""),
                    "description": item.get("snippet", {}).get("description", ""),
                    "video_id": item.get("id", {}).get("videoId", ""),
                    "video_url": f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId', '')}",
                    "thumbnail": item.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url", ""),
                }
                for item in items
            ]
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=True,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.AVAILABLE.value,
                latency_ms=latency,
                data=parsed,
                metadata={"source": "google_api_sdk", "count": len(parsed)},
            )
        except Exception:
            pass

        # 2. Direct REST fallback
        try:
            params = {
                "key": self.api_key,
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": max_results,
            }
            resp = requests.get(self.base_url, params=params, timeout=10.0)
            latency = round((time.time() - t0) * 1000, 2)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                parsed = [
                    {
                        "title": i.get("snippet", {}).get("title", ""),
                        "channel": i.get("snippet", {}).get("channelTitle", ""),
                        "video_url": f"https://www.youtube.com/watch?v={i.get('id', {}).get('videoId', '')}",
                    }
                    for i in items
                ]
                return ProviderResponse(
                    success=True,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.AVAILABLE.value,
                    latency_ms=latency,
                    data=parsed,
                    metadata={"source": "youtube_rest", "count": len(parsed)},
                )
            else:
                return ProviderResponse(
                    success=False,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.ERROR.value,
                    latency_ms=latency,
                    error=f"YouTube API returned HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"YouTube video search failed: {str(err)}",
            )
