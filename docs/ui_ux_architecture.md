# EKIP — UI/UX Architecture Specification

> **System**: Educational Knowledge Intelligence Platform (EKIP)  
> **Phase**: Phase 2.95 — Product Design & UX Architecture  
> **Document Type**: UX Architecture, Lesson Layout & Knowledge Journey Visualization  

---

## 1. Learning Page Architecture (Lesson-Centric OS Model)

Traditional conversational chatbots display a linear, ephemeral stream of chat messages. EKIP replaces chat threads with **Structured Lesson Pages** that synthesize evidence into an interactive textbook experience.

### 1.1 Structural Section Hierarchy

```
[ Topic Header & Metadata ]
      │
      ▼
[ Topic Overview & Objectives ]
      │
      ▼
[ AI Synthesis Explanation ]
      │
      ▼
[ Uploaded Course Notes & PDFs ]
      │
      ▼
[ Verified Academic Research Papers ]
      │
      ▼
[ Educational Textbooks & Books ]
      │
      ▼
[ Curated Video Lectures ]
      │
      ▼
[ Conflicting Views & Critical Analysis ]
      │
      ▼
[ Interactive Domain Glossary ]
      │
      ▼
[ Key Takeaways & Action Items ]
      │
      ▼
[ Next Recommended Learning Topics ]
```

### 1.2 Interactive Section Behaviors
- **Collapsible Cards**: Each section (Research, Books, Videos) can be expanded or collapsed to reduce cognitive load.
- **In-Line Citation Chips**: Hovering over a reference `[LeCun et al. 1998]` renders a tooltip popup displaying paper title, authors, DOI, and trust score.
- **One-Click Flashcard Generation**: Clicks on any key takeaway item allow instant conversion into an active recall flashcard.

---

## 2. EKIP Signature Feature: Knowledge Journey Graph

The **Knowledge Journey** visualizes a student's learning progression as a directed node graph rather than isolated questions.

### 2.1 Graph Layout Specification
- **Node Types**:
  - `Mastered Node` (Solid Emerald Green border, checkmark icon)
  - `In-Progress Node` (Animated Amber pulsing border, active percentage indicator)
  - `Locked / Prerequisite Node` (Muted Slate Grey border, lock icon)
- **Node Connections**:
  - `Prerequisite Edge` (Solid arrow indicating required prior knowledge)
  - `Related Topic Edge` (Dashed curve connecting tangential subjects)

```
[ Programming (Mastered) ] ────► [ Python (Mastered) ] ────► [ Data Structures (In Progress) ]
                                                                      │
                                                                      ▼
                                                            [ Algorithms (Locked) ]
```

---

## 3. Interactive Component Guidelines

- **Quick Search Command Bar (`Cmd+K` / `Ctrl+K`)**: Opens instant global search overlay to jump to any lesson, paper, flashcard deck, or course notebook.
- **Streaming Response Indicator**: Smooth skeleton placeholder loading cards with incremental section fade-ins as data streams from the server.
