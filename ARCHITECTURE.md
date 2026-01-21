# Architecture — Role-Based Approval Workflow System

## 1. Overview

This project implements a **role-based document approval workflow** using Django.
It is designed as a **learning-oriented, modular backend system** with clear separation of concerns, explicit domain rules, and auditable state transitions.

The system supports:

* Drafting and submitting documents
* Manager review and approval/rejection
* Immutable audit and approval history
* Role-based access using Django Groups

---

## 2. Architectural Principles

### 2.1 Explicit Domain Ownership

* The `Document` model owns its lifecycle.
* Status transitions are enforced at the model level.
* Views orchestrate use-cases but do not encode business rules.

### 2.2 Immutable History

* Approval decisions (`ApprovalStep`) are append-only.
* Audit logs (`AuditLog`) are append-only.
* No destructive updates of historical records.

### 2.3 Role-Based Control (RBAC)

* Roles are implemented via Django Groups:

  * Employee
  * Manager
  * Admin
* Access is enforced in views, not via Django permission flags.

### 2.4 Thin Views, Fat Models

* Views validate access and orchestrate flows.
* Models enforce invariants and transitions.

---

## 3. Application Structure

```
workflow/
├── models/
│   ├── document.py      # Core business entity
│   ├── approval.py      # Approval history
│   ├── audit.py         # Audit trail
│   └── __init__.py
│
├── views/
│   ├── document_list.py
│   ├── document_create.py
│   ├── document_update.py
│   ├── document_submit.py
│   ├── document_review_list.py
│   ├── document_decision.py
│   ├── login_redirect.py
│   └── home.py
│
├── forms.py
├── mixins.py
├── signals.py
├── urls.py
└── apps.py
```

---

## 4. Core Domain Model

### 4.1 Document

**States**

* `DRAFT`
* `SUBMITTED`
* `APPROVED`
* `REJECTED`

**Rules**

* Only draft documents can be edited.
* Only submitted documents can be approved/rejected.
* Only owners can submit.
* Only managers can decide.

**Canonical State Transition API**

```python
Document.submit()
Document.set_status(new_status, by_user)
```

---

### 4.2 ApprovalStep

Records **who decided what and when**.

* Immutable
* Ordered by decision time
* One document → many approval steps

---

### 4.3 AuditLog

Records **system actions**.

* Actor
* Action string
* Optional metadata
* Timestamped

Used for:

* Compliance
* Debugging
* Reporting (future)

---

## 5. Request Flow (High-Level)

### Employee

1. Create document → DRAFT
2. Edit while DRAFT
3. Submit → SUBMITTED

### Manager

1. View submitted documents
2. Approve or reject
3. ApprovalStep + AuditLog created atomically

---

## 6. Transaction Boundaries

Manager decisions are wrapped in:

```python
transaction.atomic()
select_for_update()
```

Guarantees:

* No double-approval
* No race conditions
* Consistent audit history

---

## 7. Authentication & Login Routing

* Django authentication is used.
* Custom `RoleBasedLoginView` redirects users based on group:

  * Managers → `/manager/documents/`
  * Others → `/documents/`

---

## 8. Templates

Templates are intentionally minimal:

* No JavaScript
* Server-rendered HTML
* Focus on correctness over appearance

---

## 9. What This Architecture Deliberately Avoids

* Django permission flags
* REST APIs
* Background workers
* UI frameworks
* Over-engineering

These may be added later **without breaking core invariants**.

---

## 10. Architecture Freeze Status

**Status:** Frozen as of commit `ed8a959`
**Changes allowed only if:**

* They preserve invariants
* They extend, not bypass, domain rules
* They do not duplicate business logic in views

---