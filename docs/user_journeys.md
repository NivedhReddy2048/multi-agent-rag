# EKIP — Persona User Journey Mapping Specification

> **System**: Educational Knowledge Intelligence Platform (EKIP)  
> **Phase**: Phase 2.95 — Product Design & UX Architecture  
> **Document Type**: End-to-End Persona Journey Mapping  

---

## 1. Primary User Personas

| Persona | Role | Primary Objectives | Key Pain Points |
|---|---|---|---|
| **Alex (Student)** | Undergraduate Computer Science | Prepare for exams, understand complex topics with evidence, practice coding and quizzes. | Scattered study notes, hallucinated AI answers, lack of structured revision paths. |
| **Dr. Sarah (Teacher)** | Associate Professor | Create courses, publish study materials, assign quizzes, monitor student comprehension. | Manual grading overhead, difficulty tracking real-time student engagement. |
| **Elena (Researcher)** | PhD Candidate | Extract research paper findings, compare conflicting evidence, spot research gaps. | Reading 100+ PDFs manually, untangling contradictory study results. |
| **Marcus (Admin)** | IT & Academic Administrator | Manage organization users, monitor platform usage, control API provider health and billing. | Security vulnerabilities, unmonitored API usage, lack of role permissions. |

---

## 2. End-to-End Persona Journeys

### 2.1 Student Journey: Exam Preparation Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Alex as Student (Alex)
    participant Dash as Dashboard
    participant Learn as Lesson Page
    participant Practice as Practice Hub
    participant Work as Workspace

    Alex->>Dash: Opens Dashboard & views "Today's Goal: Machine Learning"
    Alex->>Dash: Types query "Explain Backpropagation & Gradient Descent"
    Dash->>Learn: Navigates to Structured Lesson Page
    Learn->>Alex: Renders AI Explanation + Research Papers + Videos + Glossary
    Alex->>Learn: Clicks "Save to ML Notebook" & "Bookmark Key Takeaways"
    Learn->>Work: Saves notes to "CS 401 Notebook"
    Alex->>Practice: Launches "Generate 5-Question Quiz on Gradient Descent"
    Practice->>Alex: Displays Adaptive Quiz (Scored 80%)
    Alex->>Practice: Reviews Flashcards for missed questions
    Practice->>Dash: Updates Knowledge Journey & Increases Mastery Score (+15%)
```

---

### 2.2 Teacher Journey: Course Material & Quiz Publishing Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Sarah as Teacher (Dr. Sarah)
    participant Admin as Teacher Workspace
    participant Course as Course Manager
    participant Student as Enrolled Students

    Sarah->>Admin: Logs in & selects "CS 401: Deep Learning" Course
    Sarah->>Admin: Uploads Lecture PDF "Convolutional_Neural_Networks.pdf"
    Admin->>Course: Ingests & indexes document chunks in Cloud Storage
    Sarah->>Course: Generates Revision Cheat Sheet & Flashcard Deck using Learning Modules
    Sarah->>Course: Clicks "Publish Assignment & Quiz to CS 401 Class"
    Course->>Student: Sends Notification & assigns material to 45 enrolled students
    Sarah->>Admin: Monitors student submission rates & average score analytics
```

---

### 2.3 Researcher Journey: Evidence Extraction & Literature Synthesis

```mermaid
sequenceDiagram
    autonumber
    actor Elena as Researcher (Elena)
    participant Res as Research Hub
    participant Ver as Verification Matrix
    participant Work as Shared Workspace

    Elena->>Res: Inputs Research Prompt "Transformer Scaling Laws & Attention Bottlenecks"
    Res->>Ver: Queries ArXiv, Semantic Scholar & Jina AI in parallel
    Ver->>Elena: Displays Evidence Matrix (4 Papers Agree, 1 Disagrees)
    Elena->>Ver: Inspects Conflicting Views section
    Elena->>Work: Exports APA Citations & Research Gap Report to Shared Team Workspace
```

---

### 2.4 Administrator Journey: Platform Audit & Organization Health

```mermaid
sequenceDiagram
    autonumber
    actor Marcus as Admin (Marcus)
    participant Console as Admin Console
    participant Diag as Provider Diagnostics
    participant DB as Multi-Tenant Database

    Marcus->>Console: Logs in as Administrator
    Marcus->>Console: Inspects Active Users & Organization Quotas (85% Storage Used)
    Marcus->>Diag: Runs Health Audit across Gemini, Groq, Cohere & Mistral
    Diag->>Marcus: Flags Groq fallback rate-limiting (98% success rate overall)
    Marcus->>DB: Upgrades CS Department Subscription Plan from Free to Pro
```
