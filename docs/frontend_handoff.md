# EKIP — Developer Handoff & Frontend Architecture Specification

> **System**: Educational Knowledge Intelligence Platform (EKIP)  
> **Phase**: Phase 2.95 — Product Design & UX Architecture  
> **Document Type**: Frontend Implementation Blueprint & Handoff Guide for Phase 3.0  

---

## 1. Branding & Visual Identity Guidelines

- **Product Identity**: EKIP — AI Learning Operating System.
- **Brand Tone & Voice**: Authoritative yet encouraging, scholarly, precise, evidence-grounded, and structured.
- **Iconography**: Clean, 2px stroke line icons (`Lucide Icons` / `Heroicons`).

---

## 2. Frontend Technology Recommendations for Phase 3.0

As recommended in Phase 2.95, Streamlit has served as an exceptional prototype tool. For the production release in Phase 3.0, EKIP should be implemented using a modern production frontend stack:

```
[ Next.js 14+ / React 18+ App Router ]
           │
           ├── Tailored CSS / TailwindCSS Design Tokens
           ├── Zustand / TanStack Query (State Management & Caching)
           └── Lucide Icons / Recharts (Analytics & Graphs)
```

---

## 3. Recommended Handoff Component Structure

```
src/
 ├── components/
 │    ├── ui/              # Atom components (Button, Input, Badge, Card, Modal)
 │    ├── learn/           # Lesson Page sections (AIExplanation, ResearchList, VideoGrid)
 │    ├── practice/        # Modules (FlashcardDeck, QuizEngine, CodeEditor)
 │    └── workspace/       # Shared Library (NotebookList, DocumentIngestion)
 ├── pages / app/          # App Router Pages (/dashboard, /learn, /practice, /admin)
 ├── store/                # Client state (useUserStore, useLessonStore)
 └── lib/api/              # API Client wrappers binding to existing EKIP REST API (/api/*)
```

---

## 4. Phase 3.0 Implementation Priorities

1. **Sprint 1**: Set up Next.js project shell, design system tokens, and REST API client (`/api/auth`, `/api/users`).
2. **Sprint 2**: Implement Dashboard and Structured Learning Page layout connected to backend API router.
3. **Sprint 3**: Implement Practice Hub (Flashcards, Quizzes) and Student Workspace.
4. **Sprint 4**: Build Admin Console and Teacher Workspace with course management.
5. **Sprint 5**: Accessibility review, mobile optimization, and public launch.
