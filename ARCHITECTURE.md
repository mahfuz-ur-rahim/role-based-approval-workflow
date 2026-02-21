# Architecture.md

**Project:** RBAW – Document Approval System
**Stack:** Django 5.2 · Python 3.11 · PostgreSQL
**Architecture Style:** Layered Clean Architecture with Explicit Domain Boundaries

---

## 1. Architectural Overview

This system implements a **role-based document approval workflow** with deterministic concurrency control, structured observability, and strict permission boundaries.

The architecture follows a **Clean / Hexagonal-inspired layered model**, structured as:

```txt
Presentation Layer (Django Views + Templates)
        ↓
Application Layer (Workflow Service / Use Cases)
        ↓
Domain Layer (Entities + State Transitions)
        ↓
Infrastructure Layer (ORM, Logging, Middleware, DB)
```

The core design principle:

> The Domain layer owns business rules.
> The Application layer orchestrates use cases.
> The Presentation layer handles HTTP concerns only.
> Infrastructure supports but does not dictate behavior.

---

## 2. High-Level System Diagram

```txt
┌─────────────────────────────┐
│        Client (Browser)     │
└──────────────┬──────────────┘
               │ HTTP
┌──────────────▼──────────────┐
│     Django View Layer       │
│  (CBVs + Permission Mixins) │
└──────────────┬──────────────┘
               │ Calls
┌──────────────▼──────────────┐
│  Application / Workflow     │
│  (Document methods / svc)   │
└──────────────┬──────────────┘
               │ Mutates
┌──────────────▼──────────────┐
│       Domain Entities       │
│  Document / ApprovalStep    │
└──────────────┬──────────────┘
               │ Persists via ORM
┌──────────────▼──────────────┐
│       Infrastructure        │
│  PostgreSQL + Logging       │
└─────────────────────────────┘
```

---

## 3. Layer Responsibilities

---

## 3.1 Domain Layer (Core Business Logic)

**Location:** `workflow/models.py` (Document, ApprovalStep)
**Also:** `workflow/state_machine.py` (if present)

### Responsibilities

* Own lifecycle state
* Enforce valid transitions
* Enforce permission rules
* Prevent illegal transitions
* Guarantee deterministic concurrency behavior

### Core Entity: `Document`

#### **States**

* `DRAFT`
* `SUBMITTED`
* `APPROVED`
* `REJECTED`

### Domain Invariants

| Rule                                         | Enforced Where       |
| -------------------------------------------- | -------------------- |
| Only owner may submit draft                  | `Document.submit()`  |
| Only manager/admin may approve               | `Document.approve()` |
| Self-approval prohibited                     | `Document.approve()` |
| Only SUBMITTED can be approved/rejected      | Guard clause         |
| Only one ApprovalStep per document           | DB UniqueConstraint  |
| Single audit entry per successful transition | Service boundary     |

### Concurrency Design

The domain guarantees:

* Single winning decision under concurrent approval
* Idempotent-like behavior under race
* Atomic decision enforcement

Backed by:

* Database constraints
* Transaction isolation
* Guarded state mutation
* Tests: `test_deterministic_concurrency.py`

This ensures **linearizable approval semantics**.

---

## 3.2 Application Layer (Use Case Orchestration)

### Location

* `workflow/views/`
* Document methods (`submit`, `approve`, `reject`)

### Responsibility

Translate HTTP actions into domain transitions.

Example:

```text
POST /documents/<id>/approve/
        ↓
DocumentApproveView
        ↓
document.approve(actor)
        ↓
Domain enforces rules
        ↓
AuditLog written
```

Application layer must:

* Never duplicate business rules
* Handle exceptions and map to HTTP responses
* Emit audit logs
* Remain thin

---

## 3.3 Presentation Layer

### Components

* Django CBVs
* Templates
* Role-based navigation flags
* Group-based mixins

### Key Files

* `workflow/views/*`
* `workflow/mixins.py`
* `workflow/context_processors.py`
* `templates/`

### Functionalities

* Authentication
* Authorization boundary enforcement
* Rendering
* HTTP response codes

### Authorization Strategy

Two levels:

1. **View-level gatekeeping**

   * `ManagerRequiredMixin`
   * `ApproverRequiredMixin`
   * `AdminRequiredMixin`

2. **Domain-level enforcement**

   * Guards inside `Document.approve()`
   * Guards inside `Document.submit()`

This double-layer protection ensures defense-in-depth.

---

## 3.4 Infrastructure Layer

### Database

* PostgreSQL
* `CONN_MAX_AGE=60`
* Integrity constraints enforce invariants

### Logging

Structured JSON logging:

* Custom `JsonFormatter`
* Correlation ID middleware
* Includes:

  * actor
  * action
  * document
  * latency
  * failure flag

### Middleware

`CorrelationIdMiddleware`:

* Generates request correlation ID
* Injects into response header
* Available in structured logs

### Signals

`post_migrate` hook:

* Creates default groups

  * Employee
  * Manager
  * Admin

---

## 4. Security Architecture

### Authentication

Django auth system.

### Authorization Model

| Role      | Capabilities                   |
| --------- | ------------------------------ |
| Employee  | Create, edit own draft, submit |
| Manager   | Approve / reject (not own)     |
| Admin     | Full workflow access           |
| Superuser | Global override                |

### Enforcement Points

* View permission mixins
* Queryset scoping
* Domain guards
* 404 on cross-tenant access
* 403 on illegal state transition

This prevents:

* Horizontal privilege escalation
* Self-approval
* Cross-user audit access

---

### 5. Concurrency Model

## Objective

Guarantee deterministic single winner under concurrent decisions.

## Strategy

* Database constraint on ApprovalStep
* Atomic domain mutation
* Guarded state checks
* Race tested with real threads
* `transaction=True` test markers

## Guarantee

Under concurrent approval:

* Exactly one succeeds
* One ApprovalStep created
* One AuditLog created
* Document state consistent

---

## 6. Observability Architecture

### Structured Logging

All workflow events are logged as JSON.

Example fields:

```json
{
  "timestamp": "...",
  "level": "INFO",
  "actor": "manager",
  "document": 12,
  "action": "APPROVE",
  "correlation_id": "uuid"
}
```

### Correlation Strategy

* X-Correlation-ID header supported
* Auto-generated if missing
* Propagated to response

This enables:

* Request tracing
* Cross-service observability (future extensibility)

---

## 7. Testing Architecture

### Categories

| Type          | Purpose                   |
| ------------- | ------------------------- |
| Unit          | Domain invariants         |
| Integration   | View + domain interaction |
| Concurrency   | Race correctness          |
| Permission    | Boundary enforcement      |
| DB constraint | Integrity validation      |

### Guarantees Covered

* No double approval
* No self approval
* No duplicate steps
* Single winner under race
* No audit on failed transitions

---

## 8. Design Principles

### 1. Business Logic Isolation

No workflow rules in templates or raw views.

### 2. Deterministic State Machine

Transitions are explicit and validated.

### 3. Defense in Depth

Authorization enforced at multiple layers.

### 4. Strong Consistency

No eventual consistency; approval is atomic.

### 5. Observability First

Structured logging from the start.

---

## 9. Current Architectural Strengths

* Clear separation of concerns
* Deterministic concurrency handling
* Role-based enforcement
* Structured logging
* Comprehensive test coverage
* Clean permission boundaries

---

## 10. Known Architectural Tradeoffs

| Decision                        | Tradeoff                    |
| ------------------------------- | --------------------------- |
| Business logic in model methods | Tighter ORM coupling        |
| No service abstraction layer    | Harder to extract API later |
| Monolithic Django app           | Limited horizontal scaling  |
| Synchronous processing          | No async event stream       |

These are acceptable for current system scope.

---

## 11. Summary

This system is architected as:

> A deterministic, state-driven approval engine
> With strict domain invariants
> Enforced through layered Clean Architecture
> Backed by strong database guarantees
> And structured observability

It is production-ready in design discipline, even if feature scope is still evolving.

---
