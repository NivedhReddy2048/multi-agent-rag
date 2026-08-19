# EKIP v1.0.0 — Public Production Release Documentation

> **Platform**: Educational Knowledge Intelligence Platform (EKIP)  
> **Release Version**: `v1.0.0`  
> **Release Date**: July 31, 2026  
> **Status**: Production Release (Public Release Candidate 1)  

---

## 1. Product Summary & Architecture

EKIP is a cloud-native, multi-tenant **AI Learning Operating System** engineered to transform raw educational queries into structured, evidence-verified lesson pages, active recall practice tools, persistent workspace notebooks, and visual knowledge journey maps.

```
[ Web / Mobile Client (Next.js 14 / React 18) ]
                     │
                     ▼
  [ Backend REST API Gateway (`/api/*`) ]
                     │
 ┌───────────────────┼───────────────────┐
 ▼                   ▼                   ▼
[ Event Bus ] [ Multi-Level Cache ] [ Async Limiter ]
 (Decoupling)    (LRU & TTL)        (50+ Tasks)
                     │
                     ▼
 [ 12-Node LangGraph Educational Engine ]
   ├── Knowledge Planner & Intent Node
   ├── Multi-Agent Collection Nodes (14 Providers)
   ├── Cross-Verification & Ranking Engine
   ├── Educational Response Synthesizer
   └── Learning Module Manager (8 Plugins)
```

---

## 2. Quick Installation & Running Locally

### 2.1 Backend Server (Python 3.11+)
```bash
# Clone repository
git clone https://github.com/NivedhReddy2048/multi-agent-rag.git
cd multi-agent-rag

# Install Python dependencies
pip install -r requirements.txt

# Launch Backend App (Streamlit + REST API)
streamlit run app.py
```

### 2.2 Docker Cloud Container Launch
```bash
docker compose up -d
```
Verify status:
```bash
curl http://localhost:8501/_stcore/health
```

---

## 3. Public API Endpoint Quick Reference

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | User registration | Public |
| `POST` | `/api/auth/login` | User login & JWT issuance | Public |
| `GET` | `/api/users/me` | Fetch authenticated user profile | JWT Token |
| `POST` | `/api/courses/create` | Create a new course | Teacher / Admin |
| `GET` | `/api/courses/list` | List enrolled / created courses | JWT Token |
| `GET` | `/api/admin/metrics` | System usage analytics | Admin |

---

## 4. Benchmark Comparison Against Leading Systems

See complete benchmark report at [`docs/benchmark_report.md`](file:///d:/MultiAgentRAG-3/docs/benchmark_report.md).
