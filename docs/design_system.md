# EKIP — Design System Specification

> **System**: Educational Knowledge Intelligence Platform (EKIP)  
> **Phase**: Phase 2.95 — Product Design & UX Architecture  
> **Document Type**: Comprehensive Design System & Component Library  

---

## 1. Color Palette & Design Tokens

EKIP uses a curated dark and light mode palette tailored for prolonged reading comfort and visual clarity.

### 1.1 Dark Theme (Primary Default)
- **Background Base**: `#0B0F19` (Deep Obsidian Midnight)
- **Card / Surface**: `#111827` (Rich Dark Slate)
- **Border / Divider**: `#1F2937` (Subtle Grey Slate)
- **Primary Accent**: `#6366F1` (Indigo Blue - Intelligence)
- **Secondary Accent**: `#10B981` (Emerald Green - Mastery & Success)
- **Warning / Conflicting**: `#F59E0B` (Amber Gold - Verification Alerts)
- **Error / Blocked**: `#EF4444` (Crimson Red - System Errors)
- **Text Primary**: `#F9FAFB` (High Contrast White)
- **Text Secondary**: `#9CA3AF` (Muted Slate)

### 1.2 Light Theme
- **Background Base**: `#F9FAFB` (Soft Pure White)
- **Card / Surface**: `#FFFFFF` (Crisp White)
- **Border / Divider**: `#E5E7EB` (Clean Border)
- **Primary Accent**: `#4F46E5` (Deep Indigo)
- **Text Primary**: `#111827` (Dark Charcoal)
- **Text Secondary**: `#4B5563` (Slate Charcoal)

---

## 2. Typography Hierarchy

Primary Font Family: `Inter`, `Outfit`, `system-ui`, sans-serif.

| Level | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| **H1 Display** | 32px (2rem) | 700 (Bold) | 1.25 | Page Titles, Lesson Headers |
| **H2 Section** | 24px (1.5rem) | 600 (SemiBold) | 1.3 | Card Section Titles |
| **H3 Subsection** | 18px (1.125rem) | 600 (SemiBold) | 1.4 | Subheaders, Quiz Questions |
| **Body Large** | 16px (1rem) | 400 (Regular) | 1.6 | Main Explanation Text |
| **Body Small** | 14px (0.875rem) | 400 (Regular) | 1.5 | Metadata, Captions, Citations |
| **Code / Mono** | 13px (0.8125rem) | 400 (Regular) | 1.5 | Code Blocks, Math Equations |

---

## 3. Reusable UI Components

### 3.1 Buttons
- **Primary Button**: Background `#6366F1`, Text `#FFFFFF`, Hover `#4F46E5`, Border Radius `8px`.
- **Secondary Button**: Background `#1F2937`, Text `#F9FAFB`, Hover `#374151`, Border Radius `8px`.
- **Outline Button**: Background `Transparent`, Border `1px solid #374151`, Text `#F9FAFB`.

### 3.2 Badges & Status Chips
- **Mastered Badge**: Background `rgba(16, 185, 129, 0.15)`, Text `#10B981`, Border `1px solid #10B981`.
- **In-Progress Badge**: Background `rgba(245, 158, 11, 0.15)`, Text `#F59E0B`, Border `1px solid #F59E0B`.
- **Verified Source Chip**: Background `rgba(99, 102, 241, 0.15)`, Text `#818CF8`.

### 3.3 Cards & Containers
- Glassmorphism surface with `backdrop-filter: blur(12px)`, border `1px solid rgba(255, 255, 255, 0.08)`, and smooth elevation box shadow.
