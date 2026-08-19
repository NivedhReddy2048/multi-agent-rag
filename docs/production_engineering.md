# EKIP Phase 2.8 — Performance, Reliability & Production Engineering Specification

> **Module**: `core/events/`, `core/cache/`, `core/concurrency/`, `core/jobs/`, `core/reliability/`, `core/streaming/`, `core/security/`, `core/observability/`  
> **Version**: EKIP Phase 2.8 — Enterprise Production Engineering  

---

## 1. System Architecture Overview

EKIP Phase 2.8 transforms the platform into an enterprise-grade production software system with multi-level caching, asynchronous concurrency control, event-driven decoupling, resilience protection, and security hardening:

```
[ Student UI / Streamlit ]
           │
           ▼
[ Security Manager ] (Prompt Injection Check & Input Sanitization)
           │
           ▼
[ Multi-Level Cache Manager ] (Semantic, Planner, Retrieval, Provider, Document)
           │
           ▼
[ Async Concurrency Limiter ] (Max 50 Concurrent Provider Tasks)
           │
           ▼
[ 12-Node LangGraph Execution Graph ] (Strictly Untouched & Unchanged)
           │
           ├──────────────────────────┐
           ▼                          ▼
   [ Event Bus ]           [ Response Streamer ]
   (Decoupled Events)      (Step-by-Step Delivery)
           │                          │
           ▼                          ▼
 [ Background Jobs Queue ]  [ Student Workspace DB ]
```

---

## 2. Technical Component Specifications

### 2.1 Internal Event Bus (`core/events/`)
- In-memory publish-subscribe architecture decoupling subsystems.
- Supported Events: `EducationalResponseCreated`, `KnowledgeCollectionCompleted`, `VerificationCompleted`, `WorkspaceSaved`, `NotebookExported`, `LearningModuleCompleted`, `CacheHit`, `CacheMiss`, `ProviderFailure`, `BackgroundJobCompleted`.

### 2.2 Multi-Level Intelligent Caching (`core/cache/`)
- Multi-tier namespaces: `semantic` (2h TTL), `planner` (1h TTL), `retrieval` (30m TTL), `provider` (10m TTL), `document` (24h TTL).
- LRU eviction policy with hit/miss ratio analytics.

### 2.3 Async Execution & Concurrency Control (`core/concurrency/`)
- `AsyncConcurrencyLimiter` using `asyncio.Semaphore` to manage 50+ concurrent external API calls without system starvation.

### 2.4 Background Job System (`core/jobs/`)
- Threaded background worker queue managing jobs: PDF Indexing, Workspace Export, Research Collection, Large Document Processing, Video Metadata Collection.

### 2.5 Provider Reliability & Health Monitoring (`core/reliability/`)
- **Circuit Breaker**: Tracks failures with states `CLOSED`, `OPEN`, `HALF_OPEN` to prevent cascading outages.
- **Exponential Backoff**: Jittered retries for transient HTTP errors.
- **Health Monitor**: Real-time metrics for availability, success rate, average latency (ms), quota usage, and timestamps.

### 2.6 Security Hardening (`core/security/`)
- Prompt injection detection (regex pattern filters).
- Output sanitization (HTML escaping).
- Sensitive key masking (`AIzaSy...`, `jina_...`, `s2k_...`).

### 2.7 Observability & Telemetry (`core/observability/`)
- Request tracing with `request_id`.
- Structured audit logging (`AUDIT_EVENT`).

---

## 3. Docker & Deployment Guide

Run production container stack:
```bash
docker compose up -d
```
Check application health:
```bash
curl http://localhost:8501/_stcore/health
```
