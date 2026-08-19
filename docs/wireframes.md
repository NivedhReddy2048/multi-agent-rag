# EKIP — Low-Fidelity Wireframes Specification

> **System**: Educational Knowledge Intelligence Platform (EKIP)  
> **Phase**: Phase 2.95 — Product Design & UX Architecture  
> **Document Type**: Low-Fidelity Wireframe Documentation  

---

## 1. Low-Fidelity Wireframes

Wireframes focus strictly on spatial layout, structural visual hierarchy, component positioning, and user workflow without visual branding or colors.

---

### 1. 🏠 Dashboard Screen Wireframe

```
+-----------------------------------------------------------------------------------+
|  [EKIP Logo]  [Search Topic...               ] [🔔] [User Avatar (Alex)]           |
+-----------------------------------------------------------------------------------+
|  [Sidebar Nav] | Welcome Back, Alex! 👋                                            |
|  - Dashboard   | Today's Goal: 3/4 Tasks Completed (75%)                         |
|  - Learn       | +--------------------------------------------------------------+ |
|  - Research    | | [Continue Learning: Deep Learning & CNNs] [Resume Lesson ->]  | |
|  - Practice    | +--------------------------------------------------------------+ |
|  - Workspace   |                                                                  |
|  - Progress    | [Knowledge Journey Snapshot]       [Learning Analytics]          |
|  - Settings    | +--------------------------------+ +---------------------------+ |
|  - Admin       | | Python -> ML -> Deep Learning  | | Streaks: 5 Days 🔥       | |
|                | +--------------------------------+ | Quiz Score: 88%           | |
|                |                                    +---------------------------+ |
|                | [Workspace Shortcuts]                                            |
|                | [📄 ML Exam Notes] [📚 CS 401] [🧪 Flashcard Deck]                 |
+-----------------------------------------------------------------------------------+
```

---

### 2. 🎓 Structured Learning Page Wireframe

```
+-----------------------------------------------------------------------------------+
|  < Back to Dashboard  | Topic: Convolutional Neural Networks (CNNs)  [Bookmark] [Share] |
+-----------------------------------------------------------------------------------+
|  [Lesson Nav]  | Topic Overview                                                   |
|  - Overview    | CNNs are deep learning architectures designed for visual data.   |
|  - AI Explain  | ---------------------------------------------------------------- |
|  - Research    | AI Explanation                                                   |
|  - Books       | Key operations include convolution, pooling, and activation.    |
|  - Videos      | ---------------------------------------------------------------- |
|  - Glossary    | Research Papers & Evidence (2 Found)                              |
|  - Takeaways   | - LeCun et al. (1998) [View PDF] [Cite]                           |
|                | - Krizhevsky et al. (2012) [View PDF] [Cite]                     |
|                | ---------------------------------------------------------------- |
|                | Key Takeaways                                                    |
|                | - [ ] Feature extraction via kernels                            |
|                | - [ ] Spatial invariance using pooling layers                    |
|                | ---------------------------------------------------------------- |
|                | [Action Bar: 🧠 Practice Quiz] [🎴 Flashcards] [📝 Add Note]     |
+-----------------------------------------------------------------------------------+
```

---

### 3. 🧠 Practice Hub Wireframe

```
+-----------------------------------------------------------------------------------+
|  Practice Hub | Select Learning Module                                            |
+-----------------------------------------------------------------------------------+
|  [Module Tabs: 🎴 Flashcards | ❓ Quiz Engine | 💻 Coding | 💼 Interview Prep]       |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Question 3 / 10                                                Difficulty: Med |  |
|  | What is the primary purpose of Max Pooling in CNNs?                         |  |
|  |                                                                             |  |
|  |  ( ) A. Increase image spatial dimensions                                  |  |
|  |  (*) B. Reduce spatial dimensions & downsample feature maps                 |  |
|  |  ( ) C. Add non-linearity to the weights                                    |  |
|  |                                                                             |  |
|  |  [ Submit Answer ]                                                          |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

### 4. 📚 Workspace & Notebook Wireframe

```
+-----------------------------------------------------------------------------------+
|  Workspace Library | [My Notebooks (4)] [Shared Collections (2)] [➕ New Notebook] |
+-----------------------------------------------------------------------------------+
|  Sidebar       | CS 401 — Deep Learning Notebook                                  |
|  - ML Notes    | Last edited: 10 mins ago                                         |
|  - CNNs        | ---------------------------------------------------------------- |
|  - RNNs        | # Convolutional Neural Networks                                  |
|  - GANs        | - Kernels extract edges and shapes.                              |
|                | - Pooling reduces dimensionality.                                |
|                | ```python                                                        |
|                | model.add(Conv2D(32, (3, 3), activation='relu'))                 |
|                | ```                                                              |
|                | [ Collaborators: Alex, Dr. Sarah ] [ 🔗 Share Link ]              |
+-----------------------------------------------------------------------------------+
```

---

### 5. 🛡️ Admin & Developer Dashboard Wireframe

```
+-----------------------------------------------------------------------------------+
|  Admin Console | [System Metrics] [Users] [Courses] [Provider Health] [Cache]     |
+-----------------------------------------------------------------------------------+
|  Active Users: 1,240 | Total Courses: 42 | Storage Used: 45.2 GB (12%)            |
|  -------------------------------------------------------------------------------- |
|  Provider Health Registry Diagnostics                                             |
|  +-----------------------------------------------------------------------------+  |
|  | Provider | Status     | Configured | Avg Latency | Success Rate | Actions    |  |
|  | Gemini   | 🟢 Online  | YES        | 120 ms      | 99.8%        | [Test]     |  |
|  | Groq     | 🟢 Online  | YES        | 45 ms       | 99.5%        | [Test]     |  |
|  | Cohere   | 🟢 Online  | YES        | 180 ms      | 100%         | [Test]     |  |
|  | Mistral  | 🟡 Limited | YES        | 320 ms      | 94.2%        | [Test]     |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```
