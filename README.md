# 🧠 EKIP — Educational Knowledge Intelligence Platform

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-brightgreen.svg)](https://multi-agent-rag-rt8hvjr5qbuysvqgqtuj4x.streamlit.app/)
[![CI/CD Pipeline](https://github.com/NivedhReddy2048/multi-agent-rag/actions/workflows/ci_cd.yml/badge.svg)](https://github.com/NivedhReddy2048/multi-agent-rag/actions/workflows/ci_cd.yml)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![UI Framework](https://img.shields.io/badge/Frontend-Streamlit-red.svg)](https://streamlit.io/)
[![Orchestration](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**EKIP (Educational Knowledge Intelligence Platform)** is an evidence-driven, multi-agent Retrieval-Augmented Generation (RAG) platform designed to help students, educators, and researchers learn, practice, research, and explore educational domains.

Unlike standard single-model chatbots that generate unverified text, EKIP coordinates a **12-node LangGraph StateGraph pipeline**, a **rule-based deterministic knowledge planner**, **9 specialized knowledge source agents**, a **hybrid RAG engine (ChromaDB + BM25 + Cross-Encoder Reranking)**, and an **automated evidence verification layer** to deliver structured, grounded learning experiences.

---

## 🚀 Live Demo

🔴 **[Open EKIP — Live Application](https://multi-agent-rag-rt8hvjr5qbuysvqgqtuj4x.streamlit.app/)**

> ℹ️ **Deployment Note:** The live application is hosted on **Streamlit Community Cloud** (Python 3.11). Free cloud containers use ephemeral storage; local SQLite databases, vector caches, and uploaded documents reset when the container restarts.

---

## 📋 Table of Contents

- [Live Demo](#-live-demo)
- [Executive Project Overview](#-executive-project-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [End-to-End RAG Pipeline](#-end-to-end-rag-pipeline)
- [Source & Provider Matrix](#-source--provider-matrix)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [How the System Works (Query Flows)](#-how-the-system-works-query-flows)
- [Supported Query Intents](#-supported-query-intents)
- [Quality & Reliability Engineering](#-quality--reliability-engineering)
- [Testing & Verification](#-testing--verification)
- [Deployment & Cloud Architecture](#-deployment--cloud-architecture)
- [Environment Variables](#-environment-variables)
- [Local Development Setup](#-local-development-setup)
- [UI Screenshots](#-ui-screenshots)
- [Engineering Highlights](#-engineering-highlights)
- [Project Evolution & Roadmap](#-project-evolution--roadmap)
- [Known Limitations](#-known-limitations)
- [Security & Responsible Use](#-security--responsible-use)
- [License & Developer](#-license--developer)

---

## 💡 Executive Project Overview

### The Problem with Generic LLM Chatbots in Education
Standard large language model interfaces present several challenges when applied to education:
1. **Unverified Text Generation**: Generative models can produce plausible but inaccurate statements, formulas, or historical dates without attribution.
2. **Lack of Source Evidence**: Standard chatbots rarely cite specific passages from documents or academic literature.
3. **Unstructured Output**: Raw text outputs lack pedagogical structures such as difficulty adaptation, flashcards, study notes, or practice quizzes.
4. **Single Provider Dependency**: Reliance on a single API endpoint exposes applications to unexpected rate limits or downtime.

### The EKIP Solution
EKIP addresses these challenges by organizing planning, retrieval, verification, and synthesis into coordinated workflow stages:

```text
User Query
    │
    ▼
Knowledge Planner (Rule Engine) ──► Classifies Intent, Difficulty & Target Documents
    │
    ▼
Source Selection & Dispatch ─────► Coordinates 9 Specialized Knowledge Agents
    │
    ▼
Multi-Source Parallel Retrieval ─► Internal Docs, Web, ArXiv, Scholar, Wikipedia, YouTube, GitHub, Books
    │
    ▼
Evidence Verification ──────────► Conflict Detection, Duplicate Removal & Relevance Gating
    │
    ▼
Deterministic Evidence Ranking ──► Reciprocal Rank Fusion (RRF) + Cross-Encoder Reranking
    │
    ▼
Single Authoritative Synthesis ──► Multi-LLM Router (Groq ➔ Gemini ➔ Mistral ➔ Cohere)
    │
    ▼
Grounded Educational Response ──► Citations, Claim Entailment & Student Workspace Persistence
```

---

## ✨ Key Features

### 🧠 1. Intelligent Knowledge Planning
- **Zero-Network Deterministic Planner**: Parses user queries using zero-latency rule engines before invoking external APIs.
- **Intent Classification**: Classifies 18 educational intent types (e.g., concept explanations, research paper discovery, practice quizzes, code resource search, interview prep).
- **Difficulty Estimation**: Automatically assesses query complexity into `BEGINNER`, `INTERMEDIATE`, `ADVANCED`, or `RESEARCH`.
- **Target Document Resolution**: Matches query terms against uploaded workspace documents using stem matching and boundary rules.
- **Document Usage Modes**: Supports `REQUIRED`, `PREFERRED`, `OPTIONAL`, or `EXCLUDED` document retrieval modes.

### 🤖 2. Multi-Agent Knowledge Orchestration
EKIP coordinates 9 dedicated knowledge source agents:
- **Internal Document Agent**: Searches uploaded PDFs, DOCX, XLSX, and TXT files via hybrid RAG.
- **Trusted Web Agent**: Fetches real-time web search results via Tavily or DuckDuckGo.
- **Wikipedia Agent**: Retrieves verified encyclopedic summaries and factual background.
- **ArXiv Agent**: Queries academic preprints across Computer Science, Physics, Mathematics, and AI.
- **Semantic Scholar Agent**: Discovers peer-reviewed research literature and academic citations.
- **YouTube Agent**: Finds educational video lectures and tutorials.
- **Google Books Agent**: Recommends academic textbooks and reference literature.
- **GitHub Agent**: Searches open-source repositories and reference implementations.
- **General AI Agent**: Supplies core LLM parametric knowledge when external retrieval is unneeded.

### 📚 3. Document-Grounded Hybrid RAG
- **Multi-Format Ingestion**: Parses PDFs (`pdf2image`, `pytesseract` OCR), Word documents (`python-docx`), Excel spreadsheets (`openpyxl`), and plain text.
- **Dense & Sparse Vector Retrieval**: Combines ChromaDB dense embeddings (`sentence-transformers/all-MiniLM-L6-v2`) with sparse keyword scoring (`rank-bm25`).
- **Cross-Encoder Reranking**: Reranks retrieved candidates using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Document Filter Isolation**: Enables locking search strictly to selected workspace documents.

### 🔎 4. Evidence Verification & Grounding
- **Relevance Gating**: Filters out low-scoring or noisy chunks before synthesis.
- **Conflict & Agreement Detection**: Identifies opposing claims across diverse sources.
- **Claim-Level Entailment Evaluation**: Checks whether synthesized claims are entailments of retrieved evidence.
- **Citation Assembly**: Appends exact source attributions based on retrieved content.

### ✍️ 5. Educational Response Synthesis
- **Single Authoritative Answer Engine**: Uses a single authoritative synthesis path for clear, unified answers.
- **Multi-LLM Failover Router**: Routes generation across provider priority hierarchy:
  Groq ➔ Gemini ➔ Mistral ➔ Cohere
- **Circuit Breaker Protection**: Isolates failing API providers and recovers automatically after configurable recovery windows.

### 🎓 6. Student Workspace & Adaptive Learning
- **Learning Sessions & Notebooks**: Organizes study chats into persistent learning sessions.
- **Interactive Flashcards & Quizzes**: Generates instant practice quizzes, multiple-choice questions, and flashcard decks.
- **Study Notes & Summaries**: Transforms discussions into structured Markdown study notes.
- **Revision Assistant & Concept Graph**: Provides visual learning paths, mind maps, and interview preparation workflows.
- **Coding Practice & GitHub Discovery**: Assists with code walkthroughs, error debugging, and repository discovery.

### 📊 7. Observability & Diagnostics
- **LLM Provider Health Monitor**: Tracks latency, error rates, circuit breaker states, and availability status per provider.
- **Telemetric Query Logging**: Logs execution plans, evidence counts, rerank scores, and token latency to `observability.db`.
- **System Status Dashboard**: Displays real-time infrastructure diagnostics directly in the Streamlit UI.

### 🔐 8. Security & Isolation
- **Authentication**: User registration, login, and profile management backed by `bcrypt` password hashing and `PyJWT` tokens.
- **Secrets Protection**: Environment variables masked in logs and diagnostics. Zero API keys committed to Git.

---

## 🏗️ System Architecture

```text
                                  +-----------------------+
                                  |     User Browser      |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   Streamlit App UI    |
                                  |  (app.py / ui/ views) |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   Session / Auth Layer|
                                  | (PyJWT / SQLite Auth) |
                                  +-----------+-----------+
                                              |
                                              v
+-----------------------------------------------------------------------------------+
|                            EKIP 12-Node LangGraph DAG                            |
|                                                                                   |
|  [START] ──► [Intent Node] ──► [Difficulty Node] ──► [Source Selection Node]       |
|                                                              |                    |
|  [Execution Plan] ◄── [Output Planning] ◄── [Retrieval Strategy Node]             |
|        │                                                                          |
|        ▼                                                                          |
|  [Knowledge Collection] ──► [Verification Node] ──► [Evidence Ranking Node]       |
|                                                              │                    |
|  [END] ◄── [Workspace Persistence] ◄── [Guided Learning] ◄── [Knowledge Synthesis]|
+---------------------------------------------+-------------------------------------+
                                              |
                 +----------------------------+----------------------------+
                 |                                                         |
                 v                                                         v
  +------------------------------+                          +------------------------------+
  |    Multi-Agent Source Hub    |                          |  Multi-LLM Failover Router   |
  |  - Internal Document Agent   |                          |  1. Groq (Primary / Fast)    |
  |  - Trusted Web (Tavily/DDG)  |                          |  2. Gemini 2.5 Flash         |
  |  - Wikipedia Agent           |                          |  3. Mistral Large / Small    |
  |  - ArXiv Preprint Agent      |                          |  4. Cohere Command-R         |
  |  - Semantic Scholar Agent    |                          +------------------------------+
  |  - YouTube Video Agent       |                                         |
  |  - Google Books Agent        |                                         v
  |  - GitHub Code Agent         |                          +------------------------------+
  |  - General AI Agent          |                          |   Resilience & Protection    |
  |                              |                          |   - Circuit Breakers         |
  |                              |                          |   - Task Concurrency Limiter |
  +--------------+---------------+                          |   - Provider Health Monitor  |
                 |                                          +------------------------------+
                 v
  +------------------------------+
  | Hybrid Retrieval Engine      |
  | - ChromaDB (Dense Vector)    |
  | - Rank-BM25 (Sparse Keyword) |
  | - Cross-Encoder Reranker     |
  +------------------------------+
```

---

## 🔄 End-to-End RAG Pipeline

```text
 1. User Query Input ────────► Normalizes informal phrasing & typos (RuleBasedPlannerEngine)
 2. Intent Detection ────────► Classifies primary educational intent out of 18 types
 3. Difficulty Estimation ───► Determines BEGINNER, INTERMEDIATE, ADVANCED, or RESEARCH
 4. Target Doc Matching ─────► Matches query terms against uploaded workspace files
 5. Document Usage Mode ─────► Assigns REQUIRED, PREFERRED, OPTIONAL, or EXCLUDED
 6. Source Strategy ─────────► Selects optimal combination of 9 knowledge source agents
 7. Parallel Retrieval ──────► Dispatches tasks concurrently to selected agents
 8. Hybrid Search Gating ────► Combines ChromaDB dense vector search + BM25 sparse retrieval
 9. Cross-Encoder Reranking ──► Reranks retrieved chunks via CrossEncoder model
10. Evidence Verification ───► Filters low-quality chunks & checks claim conflicts
11. Multi-LLM Routing ──────► Selects active LLM provider via priority failover hierarchy
12. Prompt Engineering ──────► Builds educational prompt with authority-ranked evidence
13. Knowledge Synthesis ─────► Synthesizes authoritative response with inline citations
14. Claim Grounding Check ───► Evaluates claim entailment against retrieved sources
15. Workspace Persistence ──► Stores session state, notes, flashcards, & analytics
```

---

## 📊 Source & Provider Matrix

| Provider / Source | Role | Category | Key Required? | Notes |
|---|---|---|:---:|---|
| **Groq** | LLM Generation | Primary LLM | Yes | High-speed inference (Llama-3 models) |
| **Google Gemini** | LLM Generation | Secondary LLM | Yes | Primary multimodal LLM (`gemini-2.5-flash`) |
| **Mistral AI** | LLM Generation | Fallback LLM | Yes | Reasoning fallback (`mistral-large-latest`) |
| **Cohere** | LLM Generation | Fallback LLM | Yes | Command-R fallback model |
| **Tavily AI** | Web Search | Factual Evidence | Yes | Web search for CRAG agent |
| **DuckDuckGo** | Web Search | Factual Evidence | **No** | Free web search fallback |
| **Wikipedia** | General Knowledge | Factual Evidence | **No** | Open public encyclopedic API |
| **ArXiv** | Academic Research | Factual Evidence | **No** | Open academic preprint database |
| **Semantic Scholar** | Research Literature | Factual Evidence | Optional | Academic paper search |
| **YouTube** | Educational Video | Resource Discovery | Optional | Video lecture discovery via Data API |
| **Google Books** | Literature Search | Resource Discovery | Optional | Textbook & reference literature search |
| **GitHub** | Open-Source Code | Resource Discovery | Optional | Repository & implementation search |
| **Jina Reader** | Web Extraction | Utility | Optional | Clean markdown web scraping |
| **Firecrawl** | Web Crawling | Utility | Optional | Web site crawling |
| **SerpAPI** | Search Engine | Utility | Optional | Google Search fallback API |

---

## 🛠️ Technology Stack

| Domain | Technology / Library | Usage in EKIP |
|---|---|---|
| **Language** | Python 3.11 | Core runtime environment |
| **UI Framework** | Streamlit 1.40+ | Interactive web interface & dashboard |
| **Orchestration** | LangGraph & LangChain 0.3+ | 12-Node DAG state machine & agent workflows |
| **Vector Database** | ChromaDB 0.5+ | Local persistent dense vector storage |
| **Dense Embeddings** | Sentence-Transformers | `sentence-transformers/all-MiniLM-L6-v2` |
| **Sparse Retrieval** | Rank-BM25 | BM25 keyword search scoring |
| **Cross-Encoder Reranker**| Transformers / PyTorch | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **LLM Provider SDKs** | `langchain-google-genai`, `langchain-groq`, `langchain-cohere`, `langchain-mistralai` | Multi-provider LLM integrations |
| **Document Processing** | `pdf2image`, `pytesseract`, `unstructured`, `python-docx`, `openpyxl`, `pandas`, `Pillow` | Multi-format document parsing & OCR |
| **Database & Auth** | SQLite, `PyJWT`, `bcrypt` | Local state persistence & secure authentication |
| **Testing** | `pytest` | Comprehensive unit, integration, and E2E tests |
| **Deployment** | Streamlit Community Cloud | Cloud hosting container (`packages.txt`, `.streamlit/config.toml`) |
| **CI/CD** | GitHub Actions | Automated build, lint, test, and Docker verification |

---

## 📂 Project Structure

```text
multi-agent-rag/
├── .github/
│   └── workflows/
│       └── ci_cd.yml                 # GitHub Actions CI/CD pipeline
├── .streamlit/
│   └── config.toml                   # Streamlit Community Cloud server & theme config
├── agents/
│   ├── orchestrator.py               # Main multi-agent orchestrator & dispatch engine
│   ├── crag.py                       # Corrective RAG (CRAG) fallback agent
│   ├── synthesis.py                  # Knowledge synthesis agent
│   ├── validation.py                 # Evidence verification & grounding agent
│   └── sources/                      # 9 Specialized Knowledge Source Agents
│       ├── arxiv_agent.py
│       ├── document_agent.py
│       ├── general_ai_agent.py
│       ├── github_agent.py
│       ├── google_books_agent.py
│       ├── semantic_scholar_agent.py
│       ├── trusted_web_agent.py
│       ├── wikipedia_agent.py
│       └── youtube_agent.py
├── analytics/                        # Telemetry & query analytics modules
├── config/
│   └── settings.py                   # Centralized application configuration & env defaults
├── core/
│   ├── config.py                     # EKIP typed configuration manager
│   ├── engine.py                     # Hybrid RAG engine (ChromaDB + BM25 + Reranker)
│   ├── logger.py                     # Structured Loguru logging setup
│   ├── auth/                         # User authentication, database & JWT session management
│   ├── llm/                          # Multi-LLM router, CircuitBreaker, & HealthMonitor
│   ├── models/                       # Pydantic domain models & state definitions
│   ├── observability/                # Performance metrics, query logging & telemetry DB
│   ├── planner/                      # Rule-based deterministic planning engine & enums
│   ├── reliability/                  # Event bus, concurrency limiters & recovery managers
│   └── retrieval/                    # Multi-format document loaders & text splitters
├── graph/
│   ├── builder.py                    # LangGraph StateGraph 12-node DAG builder
│   ├── state.py                      # EKIPGraphState state schema
│   └── nodes/                        # Individual DAG step node functions
├── ui/                               # Streamlit UI components & views
│   ├── views/                        # Workspace, Chat, Analytics, Profile, Diagnostics views
│   └── components/                   # Reusable UI widgets & sidebars
├── tests/                            # 61 test modules (Unit, Integration, & E2E)
├── app.py                            # Main Streamlit application entrypoint
├── Dockerfile                        # Production Docker container build
├── packages.txt                      # Debian Linux system dependencies for cloud deployment
├── requirements.txt                  # Python package requirements
├── render.yaml                       # Render deployment template
└── README.md                         # Project documentation
```

---

## 🔄 How the System Works (Query Flows)

### 1. General Knowledge Query Flow
```text
User: "Explain Quantum Entanglement in simple terms"
  │
  ├──► Planner: Intent = CONCEPT_EXPLANATION | Difficulty = BEGINNER | Mode = EXCLUDED
  ├──► Source Selection: General AI + Wikipedia
  ├──► Parallel Retrieval: Wikipedia API + Core LLM
  ├──► Verification: Relevance score checked
  ├──► Synthesis: Groq/Gemini generates structured response with analogies
  └──► UI Render: Displays explanation + citation links + option to generate flashcards
```

### 2. Document-Grounded Question Flow
```text
User: "Summarize section 3 of my uploaded lecture notes"
  │
  ├──► Planner: Intent = DOCUMENT_QUERY | TargetDocs = ["lecture_notes.pdf"] | Mode = REQUIRED
  ├──► Source Selection: Internal Document Agent
  ├──► Hybrid Search: ChromaDB dense vector search + BM25 keyword matching
  ├──► Reranking: Cross-Encoder scores top chunks
  ├──► Synthesis: Generates answer grounded in document context
  └──► UI Render: Answers query with text snippet attributions
```

### 3. Academic Research Query Flow
```text
User: "Find recent research papers on Transformer Cross-Attention"
  │
  ├──► Planner: Intent = RESEARCH_DISCOVERY | Difficulty = RESEARCH | Mode = EXCLUDED
  ├──► Source Selection: ArXiv Agent + Semantic Scholar Agent + Trusted Web
  ├──► Retrieval: Fetches preprints, authors, publication dates, & abstracts
  ├──► Ranking: Ranks papers by citation count and semantic relevance
  └──► UI Render: Formats paper survey table with PDF links and synthesis summary
```

---

## 🎯 Supported Query Intents

EKIP's deterministic rule engine classifies user queries into 18 supported intent categories:

| Educational Intent Enum | Primary Trigger Keywords / Patterns | Expected Output Format |
|---|---|---|
| `CONCEPT_EXPLANATION` | "what is", "explain", "define", "concept of" | Detailed Explanation |
| `DOCUMENT_QUERY` | "my document", "uploaded pdf", "in my notes", "this file" | Study Notes / Attributed Answer |
| `RESEARCH_DISCOVERY` | "paper", "arxiv", "semantic scholar", "preprints", "literature" | Research Survey Table |
| `PRACTICE_QUIZ` | "practice quiz", "test questions", "quiz me" | Interactive Quiz Widget |
| `QUIZ_GENERATION` | "quiz", "test me", "generate questions", "mcq" | Interactive Quiz Widget |
| `PROGRAMMING_HELP` | "write code", "how to fix", "debug error", "python script" | Code Walkthrough |
| `CODE_RESOURCE_RECOMMENDATION` | "github", "open source repo", "reference implementation" | Code Walkthrough & Repos |
| `INTERVIEW_PREPARATION` | "interview questions", "mock question", "interview prep" | Interview QA Breakdown |
| `CAREER_GUIDANCE` | "how to become", "career path", "skills needed for" | Career Roadmap |
| `COMPARISON` | "compare", "versus", "difference between", "vs" | Comparison Table |
| `ROADMAP` | "learning path", "curriculum", "roadmap" | Learning Roadmap |
| `BOOK_RECOMMENDATION` | "book", "textbook", "reading list" | Book Recommendation List |
| `VIDEO_RECOMMENDATION` | "youtube", "video tutorial", "watch" | Video Recommendation List |
| `STUDY_NOTES` | "study notes", "summarize notes", "lecture notes" | Markdown Study Notes |
| `FLASHCARDS` | "flashcards", "memo cards" | Interactive Flashcards |
| `TOPIC_SUMMARY` | "summarize topic", "overview of" | Summary Breakdown |
| `WEB_INFORMATION` | "latest", "recent news", "today", "current online" | Web Information Summary |
| `FOLLOW_UP` | "that second point", "more on that", "what did you mean" | Contextual Follow-Up Response |

---

## 🛡️ Quality & Reliability Engineering

EKIP is built with software engineering patterns for resilience:

1. **Deterministic Planning**: Rule engines make zero-latency routing decisions without expensive, non-deterministic LLM function calls.
2. **Provider Failover & Circuit Breakers**: If a primary LLM provider (e.g. Groq) encounters an outage, EKIP automatically shifts traffic to Gemini, Mistral, or Cohere. The failed provider is isolated by a `CircuitBreaker` pattern to improve resilience during provider degradation.
3. **Concurrency Limiter**: Multi-agent retrieval calls are throttled using asynchronous semaphore limiters (`MAX_CONCURRENT_PROVIDER_TASKS`) to prevent API rate-limit errors.
4. **Strict Grounding Enforcement**: When users request document-locked mode (`REQUIRED`), EKIP restricts external model output by enforcing strict context boundaries.
5. **Unicode Console Safety**: Telemetry logging includes safe encoding handlers to prevent OS-level terminal issues on Windows environments.

---

## 🧪 Testing & Verification

EKIP includes **61 test modules** in the `tests/` directory covering unit, integration, performance, and acceptance testing.

### Key Test Batteries:
- **Production Engineering Battery**: `tests/test_production_engineering.py` (verifies EventBus, MultiLevelCache, ConcurrencyLimiter, CircuitBreaker, and SecurityManager).
- **Knowledge Planner Tests**: `tests/test_knowledge_planner.py`, `tests/test_source_strategy_planner.py`
- **Knowledge Verification & Synthesis**: `tests/test_knowledge_verification.py`, `tests/test_knowledge_synthesis.py`
- **Provider Resilience**: `tests/test_llm_provider_reliability.py`, `tests/test_provider_resilience.py`
- **Student Workspace Tests**: `tests/test_student_workspace.py`, `tests/test_learning_modules.py`

### Running Tests Locally:

```bash
# Run the core production engineering test battery
python -m pytest tests/test_production_engineering.py

# Run the complete test suite
python -m pytest tests/
```

### GitHub Actions CI/CD Pipeline
Every push to `main` triggers `.github/workflows/ci_cd.yml` to automatically verify dependencies, run integration tests, and validate Docker builds.

---

## ☁️ Deployment & Cloud Architecture

### Live Deployment Configuration
EKIP is configured for automated deployment on **Streamlit Community Cloud**:

- **Repository**: `NivedhReddy2048/multi-agent-rag`
- **Branch**: `main`
- **Entrypoint**: `app.py`
- **Python Runtime**: `3.11`
- **System Packages (`packages.txt`)**: Includes `tesseract-ocr`, `poppler-utils`, and `build-essential` for PDF OCR and Linux image processing.
- **Server Config (`.streamlit/config.toml`)**: Enables headless execution and sets the UI dark theme.

### ⚠️ Ephemeral Cloud Storage Limitation
On free hosting platforms like Streamlit Community Cloud:
- Containers run on **ephemeral disk instances**.
- Local SQLite databases (`ekip_users.db`, `observability.db`), uploaded files in `data/uploads/`, and Chroma vector collections in `data/chroma_db/` will reset whenever the cloud container restarts or rebuilds.
- This is an architectural constraint of free-tier cloud hosting.

---

## 🔐 Environment Variables

Create a local `.env` file based on `.env.example`:

```env
# Core API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Knowledge Source Keys (Optional)
GITHUB_TOKEN=your_github_personal_access_token
SERPAPI_API_KEY=your_serpapi_key
FIRECRAWL_API_KEY=your_firecrawl_key
JINA_API_KEY=your_jina_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key
YOUTUBE_DATA_API_KEY=your_youtube_api_key
GOOGLE_BOOKS_API_KEY=your_google_books_key
DUCKDUCKGO_ENABLED=true

# System & Performance Tuning
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENV_MODE=production
MAX_CONCURRENT_PROVIDER_TASKS=50
CIRCUIT_BREAKER_THRESHOLD=3
CIRCUIT_BREAKER_RECOVERY_SEC=30.0
```

---

## 💻 Local Development Setup

Follow these steps to run EKIP locally:

```bash
# 1. Clone the repository
git clone https://github.com/NivedhReddy2048/multi-agent-rag.git
cd multi-agent-rag

# 2. Create a Python 3.11 virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure environment variables
copy .env.example .env
# Edit .env and insert your API keys

# 6. Launch the Streamlit application
streamlit run app.py
```

The application will be accessible locally at `http://localhost:8501`.

---

## 🖼️ UI Screenshots

> Screenshots will be added in a future documentation update.

---

## 🌟 Engineering Highlights

1. **Deterministic Rule Engine over Probabilistic Intent Routing**: Reduces router latency and eliminates routing hallucinations by using zero-latency regex stem matching for intent and target document resolution.
2. **Hybrid RAG Fusion**: Combines ChromaDB dense semantic vector search with BM25 sparse keyword matching and Cross-Encoder reranking for document precision.
3. **Resilient Multi-LLM Router**: Features circuit breaking and fallback cascading across 4 major LLM providers to maintain service continuity during provider degradation.
4. **Modular Agent Design**: Decouples retrieval agents into 9 specialized source workers, allowing independent maintenance.

---

## 📈 Project Evolution & Roadmap

### Project Milestones Achieved
- [x] Enterprise RAG Architecture & Vector Indexing
- [x] 12-Node LangGraph StateGraph Orchestration Implementation
- [x] Multi-LLM Provider Router with Circuit Breakers
- [x] 9 Specialized Knowledge Source Agents
- [x] Student Workspace with Flashcards, Quizzes, & Study Notes
- [x] Telemetric Observability & Diagnostic Dashboards
- [x] Streamlit Community Cloud Deployment

### Future Roadmap
- [ ] **Durable Database Integration**: Migration from local SQLite to hosted PostgreSQL (Supabase / Neon DB) for cloud user persistence.
- [ ] **Distributed Vector Store**: Integration with Qdrant or Pinecone for cloud vector persistence across container reboots.
- [ ] **Background Job Workers**: Offloading long research papers and heavy PDF OCR tasks to background worker queues.
- [ ] **Multilingual Learning Modules**: Translation and adaptive language support for global students.

---

## ⚠️ Known Limitations

1. **Ephemeral Storage on Free Cloud**: Uploaded files, user database entries, and vector caches reset when Streamlit Cloud restarts the container instance.
2. **API Provider Rate Limits**: If external API keys hit rate limits, the system gracefully falls back to DuckDuckGo or General AI.
3. **Resource Constraints**: Cloud resource constraints may affect heavy document ingestion or large workloads on free hosting.

---

## 🔒 Security & Responsible Use Note

- **Educational & Research Purpose**: EKIP is designed as an educational assistant and research exploration platform.
- **Evidence Verification**: While EKIP implements evidence verification and claim entailment scoring, AI-generated responses should be cross-referenced with primary cited sources.
- **Data Protection**: API keys and personal credentials should never be committed to repository code or public files.

---

## 📄 License & Developer

### License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

### Developer & Author
**Nivedh Reddy**
- **GitHub**: [github.com/NivedhReddy2048](https://github.com/NivedhReddy2048)
- **Repository**: [github.com/NivedhReddy2048/multi-agent-rag](https://github.com/NivedhReddy2048/multi-agent-rag)
- **Live Platform**: [multi-agent-rag-rt8hvjr5qbuysvqgqtuj4x.streamlit.app](https://multi-agent-rag-rt8hvjr5qbuysvqgqtuj4x.streamlit.app/)
