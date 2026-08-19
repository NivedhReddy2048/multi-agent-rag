# EKIP — Responsive Design Strategy Specification

> **System**: Educational Knowledge Intelligence Platform (EKIP)  
> **Phase**: Phase 2.95 — Product Design & UX Architecture  
> **Document Type**: Responsive Breakpoint & Adaptation Specification  

---

## 1. Breakpoint Grid Specification

| Device Tier | Viewport Width | Sidebar Behavior | Layout Strategy |
|---|---|---|---|
| **Desktop / Widescreen** | `>= 1200px` | Fixed Expanded (260px) | 3-Column Layout (Nav + Content + Inspector) |
| **Tablet / Laptop** | `768px - 1199px` | Collapsed Icons-Only (64px) | 2-Column Layout (Nav + Main Content) |
| **Mobile Device** | `< 768px` | Hidden Drawer (Bottom Nav) | 1-Column Stacked Cards |

---

## 2. Navigation Adaptations

### 2.1 Desktop Layout (`>= 1200px`)
- Left sidebar remains permanently visible with section labels and icons.
- Top action header displays persistent search bar (`Cmd+K`) and profile status.

### 2.2 Mobile Layout (`< 768px`)
- Left sidebar converts to a fixed bottom navigation bar with 5 primary icons: 🏠 Dashboard, 🎓 Learn, 🧠 Practice, 📚 Workspace, ⚙ Settings.
- Tables auto-enable horizontal scroll containers (`overflow-x: auto`).
