# EKIP — Accessibility & Motion Guidelines Specification

> **System**: Educational Knowledge Intelligence Platform (EKIP)  
> **Phase**: Phase 2.95 — Product Design & UX Architecture  
> **Document Type**: WCAG 2.1 AA Accessibility & Interaction Motion Specification  

---

## 1. WCAG 2.1 AA Accessibility Standards

1. **Color Contrast Ratio**:
   - Text to background contrast must satisfy minimum **4.5:1** for standard text and **3:1** for large heading displays.
2. **Keyboard Focus Management**:
   - Visible focus rings (`2px solid #6366F1` with `2px offset`) on all interactive buttons, inputs, links, and card tabs.
3. **Screen Reader ARIA Attributes**:
   - Dynamic content updates (like streaming responses) must use `aria-live="polite"`.
   - Modals and expandable sections must utilize `aria-expanded="true/false"` and `aria-modal="true"`.

---

## 2. Motion & Micro-Animation Guidelines

- **Page Transitions**: Subdued fade-in (`opacity: 0 -> 1` over `200ms ease-out`).
- **Card Expansion**: Smooth height transition (`max-height: 0 -> 500px` over `300ms cubic-bezier(0.4, 0, 0.2, 1)`).
- **Reduced Motion Preference (`prefers-reduced-motion: reduce`)**:
  - Automatically disables all spring and bounce animations, substituting instant opacity fades.
