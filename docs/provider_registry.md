# EKIP Provider Registry Specification

> **Module**: `core/providers`  
> **Version**: EKIP Phase 2.1 — Infrastructure & Integration Layer

---

## 1. Overview

The **EKIP Provider Registry** establishes a centralized, production-quality infrastructure for managing all current and future knowledge providers across multiple categories (General AI, Web Search, Extraction, Reader, Academic Literature, Media, Books, and Repositories).

This layer is infrastructure-only. It does **not** alter the core RAG pipeline, CRAG, Conversation Memory, Telemetry, or UI behavior, ensuring full backward compatibility while preparing EKIP for Phase 2 multi-agent orchestration.

---

## 2. Knowledge Provider Matrix

| Provider Identifier | Name | Category | Auth Requirement | Optional / Required | Intended Future Phase Use |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `gemini` | Google Gemini API | `LLM` | `GEMINI_API_KEY` | Required (Primary) | Primary baseline LLM synthesis engine |
| `groq` | Groq Llama-3 API | `LLM` | `GROQ_API_KEY` | Optional | Ultra-fast inference & fast fallback synthesis |
| `cohere` | Cohere Command-R | `LLM` | `COHERE_API_KEY` | Optional | Secondary fallback synthesis engine |
| `mistral` | Mistral Large/Small | `LLM` | `MISTRAL_API_KEY` | Optional | Tertiary fallback synthesis engine |
| `tavily` | Tavily Web Search API | `SEARCH` | `TAVILY_API_KEY` | Optional | Primary real-time web knowledge collector |
| `duckduckgo` | DuckDuckGo / SerpApi | `SEARCH` | `SERPAPI_API_KEY` (Optional) | Optional | Fallback search when Tavily is rate-limited |
| `firecrawl` | Firecrawl API | `EXTRACTION` | `FIRECRAWL_API_KEY` | Optional | Structured webpage scraping & extraction |
| `jina` | Jina AI Reader API | `READER` | `JINA_API_KEY` (Optional) | Optional | Markdown web content extraction (`r.jina.ai`) |
| `semantic_scholar`| Semantic Scholar Graph| `ACADEMIC` | `SEMANTIC_SCHOLAR_API_KEY` | Optional | Academic research paper title/abstract search |
| `wikipedia` | Wikipedia MediaWiki | `ACADEMIC` | Public Open API (No Key) | Required (Open) | Educational definitions & overview facts |
| `arxiv` | arXiv Export API | `ACADEMIC` | Public Open API (No Key) | Required (Open) | Open-access scientific research paper search |
| `youtube` | YouTube Data API v3 | `VIDEO` | `YOUTUBE_DATA_API_KEY` | Optional | Educational video recommendations |
| `google_books` | Google Books API v1 | `BOOKS` | `GOOGLE_BOOKS_API_KEY` | Optional | Book literature & preview link search |
| `github` | GitHub REST API v3 | `REPOSITORY` | `GITHUB_TOKEN` | Optional | Code repository & technical doc search |

---

## 3. Provider Standardized Interface

All 14 providers inherit from `BaseProvider` (`core/providers/base.py`) and expose:

- `initialize() -> bool`: Validates credentials and initializes SDKs/clients.
- `health_check() -> ProviderResponse`: Returns real-time health, latency (ms), and status (`Ready (Not yet used)`, `Available`, `Not Configured`, or `Error`).
- `search(query: str, **kwargs) -> ProviderResponse`: Executes search query returning standardized `ProviderResponse`.
- `fetch(identifier: str, **kwargs) -> ProviderResponse`: Fetches/extracts URL or document content returning standardized `ProviderResponse`.
- `close() -> None`: Releases network resources.

---

## 4. Standardized Response Model (`ProviderResponse`)

```python
class ProviderResponse(BaseModel):
    success: bool
    provider: str
    category: ProviderCategory
    status: str
    latency_ms: float = 0.0
    error: Optional[str] = None
    data: Any = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

---

## 5. Security & Masking Protocol

To prevent raw secret leakage in telemetry, terminal logs, or UI diagnostics:
- API keys are loaded via `.env` through `core/config.py`.
- Keys are masked via `Config.get_masked_key(provider_name)` (e.g. `jina_9...Wgsm`).
- Open APIs (`wikipedia`, `arxiv`) explicitly return `PUBLIC_API (No Key Required)`.

---

## 6. Rate Limit & Error Handling Guidelines

1. **Structured Fallbacks**: Operations catch SDK/HTTP errors internally and return `ProviderResponse(success=False, error=...)` instead of raising raw exceptions.
2. **Circuit Safety**: Health checks default unused optional providers to status `"Ready (Not yet used)"` rather than marking them as errors when uncalled.
