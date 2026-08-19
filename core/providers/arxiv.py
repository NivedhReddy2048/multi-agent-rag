"""arXiv Open Access Research Paper Provider Wrapper (No API Key Required)."""

import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class ArxivProvider(BaseProvider):
    """arXiv Research Provider integration wrapper (Public Open Access API)."""

    def __init__(self):
        super().__init__(name="arxiv", category=ProviderCategory.ACADEMIC, is_optional=False)

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health_check(self) -> ProviderResponse:
        t0 = time.time()
        self.initialize()
        latency = round((time.time() - t0) * 1000, 2)
        return ProviderResponse(
            success=True,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.READY.value,
            latency_ms=latency,
            data={"configured": True, "type": "Public Open API (No API Key Required)"},
            metadata={"public": True},
        )

    def search(self, query: str, max_results: int = 5, **kwargs) -> ProviderResponse:
        t0 = time.time()
        # 1. Try official arxiv Python SDK
        try:
            import arxiv
            client = arxiv.Client()
            search_query = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            results = list(client.results(search_query))
            parsed = [
                {
                    "title": paper.title,
                    "authors": [a.name for a in paper.authors],
                    "published": paper.published.strftime("%Y-%m-%d") if paper.published else "",
                    "summary": paper.summary,
                    "pdf_url": paper.pdf_url,
                    "entry_id": paper.entry_id,
                }
                for paper in results
            ]
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=True,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.AVAILABLE.value,
                latency_ms=latency,
                data=parsed,
                metadata={"source": "arxiv_sdk", "count": len(parsed)},
            )
        except Exception:
            pass

        # 2. Fallback to arXiv Export REST API
        try:
            url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
            }
            resp = requests.get(url, params=params, timeout=10.0)
            latency = round((time.time() - t0) * 1000, 2)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = []
                for entry in root.findall("atom:entry", ns):
                    title = entry.find("atom:title", ns)
                    summary = entry.find("atom:summary", ns)
                    published = entry.find("atom:published", ns)
                    authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]
                    entries.append({
                        "title": title.text.strip() if title is not None else "",
                        "authors": authors,
                        "published": published.text[:10] if published is not None else "",
                        "summary": summary.text.strip() if summary is not None else "",
                        "pdf_url": "",
                    })
                return ProviderResponse(
                    success=True,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.AVAILABLE.value,
                    latency_ms=latency,
                    data=entries,
                    metadata={"source": "arxiv_rest_xml", "count": len(entries)},
                )
            else:
                return ProviderResponse(
                    success=False,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.ERROR.value,
                    latency_ms=latency,
                    error=f"arXiv REST HTTP {resp.status_code}",
                )
        except Exception as err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"arXiv search error: {str(err)}",
            )
