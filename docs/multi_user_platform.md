# EKIP Phase 2.9 — Multi-User Educational SaaS Platform Specification

> **Module**: `core/auth/`, `core/db/`, `core/storage/`, `core/rbac/`, `core/courses/`, `core/collaboration/`, `core/admin/`, `core/billing/`, `api/`  
> **Version**: EKIP Phase 2.9 — Multi-Tenant Educational SaaS Architecture  

---

## 1. System Architecture Overview

EKIP Phase 2.9 transforms the platform into a cloud-native, multi-tenant educational platform supporting students, teachers, administrators, researchers, and organizations:

```
[ Web / Mobile / Desktop Clients ]
               │
               ▼
       [ REST API Layer ] (/api/auth, /api/users, /api/courses, /api/admin)
               │
      ┌────────┴────────┐
      ▼                 ▼
[ Auth Manager ]   [ RBAC Manager ] (Admin, Teacher, Student, Researcher, Guest)
(JWT Tokens)            │
                        ▼
            [ Course & Organization Manager ]
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
   [ Cloud Storage ]       [ PostgreSQL / SQLite ]
   (Local, S3, Azure, GCS) (Dual Database Engine)
```

---

## 2. Component Specifications

### 2.1 Authentication & Identity (`core/auth/`)
- User registration, login/logout, salted SHA-256 password hashing, JWT token issuance & blacklisting.
- User Roles: `administrator`, `teacher`, `student`, `researcher`, `guest`.

### 2.2 Database Engine Dual Support (`core/db/`)
- Dual backend support for SQLite (`sqlite:///...`) in local development and PostgreSQL (`postgresql://...`) in production environments.

### 2.3 Cloud Storage Abstraction (`core/storage/`)
- Unified `StorageProvider` abstraction supporting `LocalStorageProvider`, `S3StorageProvider` (AWS S3), `AzureBlobStorageProvider` (Azure Blob), and `GCSStorageProvider` (Google Cloud Storage).

### 2.4 Role-Based Access Control (`core/rbac/`)
- Centralized permission mapping for system capabilities (`course:create`, `student:monitor`, `quiz:assign`, `admin:console`).

### 2.5 Course & Shared Collaboration (`core/courses/` & `core/collaboration/`)
- Teacher course creation, student enrollment, study material publishing, quiz assignments.
- Team shared notebooks, collections, and bookmarks.

### 2.6 SaaS Monetization & Billing (`core/billing/`)
- Subscription tiers: `Free` (50 queries/day, 100MB storage), `Pro` (1,000 queries/day, 5GB storage), `Enterprise` (100,000 queries/day).
- Feature gating and quota enforcement via `BillingManager.check_feature_access()`.

---

## 3. REST API Reference

| Endpoint | Method | Role Required | Description |
|---|---|---|---|
| `/api/auth/register` | POST | Public | Register new user account |
| `/api/auth/login` | POST | Public | Authenticate user & issue JWT token |
| `/api/users/me` | GET | Any User | Fetch authenticated user profile |
| `/api/courses/create` | POST | Teacher / Admin | Create a new course |
| `/api/courses/list` | GET | Student / Teacher | List enrolled / created courses |
| `/api/admin/metrics` | GET | Admin | Fetch system usage metrics |
