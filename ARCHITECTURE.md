# Architecture Overview

## Role-Based Document Approval Workflow System

## 1. Architectural Goals

This system is designed to demonstrate a **secure, auditable, role-based approval workflow** with explicit enforcement of separation of duties. The architecture prioritizes:

- Clear responsibility boundaries between roles
- Explicit workflow state transitions
- Auditability of all sensitive actions
- Defense-in-depth (UI, view, and data-layer checks)
- Educational clarity over framework “magic”

---

## 2. Core Domain Model

### Document Lifecycle

Documents move through a **strict, linear lifecycle**:

```txt
DRAFT → SUBMITTED → APPROVED / REJECTED
```

Transitions are:

- Explicit
- Atomic
- Audited
- Permission-checked

No implicit state changes exist.

---

## 3. Roles and Responsibilities

Roles are implemented using **Django Groups**.

| Role     | Capabilities                                            |
|----------|---------------------------------------------------------|
| Employee | Create, edit (draft), submit documents                  |
| Manager  | All Employee actions + approve/reject others’ documents |
| Admin    | All Manager actions + system-wide audit visibility      |

### Important Rules

- **Admins are approvers**, not automatic approvers.
- **No role can approve its own documents**.
- Superusers bypass group checks but are still blocked from self-approval.

---

## 4. Permission Architecture

### 4.1 View-Level Enforcement (Primary)

Permissions are enforced using **explicit mixins**, not decorators or template logic.

#### GroupRequiredMixin

Base mixin for group-based access control.

```python
class GroupRequiredMixin(UserPassesTestMixin):
    required_groups: list[str]
```

Used to define:

- `EmployeeRequiredMixin`
- `ManagerRequiredMixin`
- `AdminRequiredMixin`
- `ApproverRequiredMixin`

#### ApproverRequiredMixin

Allows access to approval actions for:

- Managers
- Admins

Self-approval is **explicitly forbidden at the view level**, not in the mixin.

### 4.2 Separation of Duties (Defense-in-Depth)

Self-approval prevention is enforced in **two layers**:

1. **Queryset filtering**  

```python
    .exclude(created_by=self.request.user)
```

1. **Transactional check**  

```python
   if document.created_by_id == request.user.id:
       raise Http404
```

This ensures:

- UI bypasses are ineffective
- Concurrent approval attempts are safe
- Integrity is preserved under race conditions

### 4.3 Authorization & Error Semantics

The system enforces strict separation between:

- **Visibility (404)** – A user must not be able to infer the existence of documents outside their permitted boundary.
  - Employees may only see their own documents.
  - Managers and Admins may see all documents.
  - Unauthorized visibility attempts return 404.

- **Authorization (403)** – If a user can see a document but is not permitted to perform a specific action (e.g., self-approval), the system returns 403.

- **Workflow Invalid State (400)** – If an authorized user attempts a state transition that is not allowed by the pure state machine, the system returns 400.

**Invariant:** View-layer logic must enforce visibility before invoking `DocumentWorkflowService`. The service layer remains the single mutation authority.

### 4.4 Data Integrity Guarantees

Database-level constraints mirror workflow invariants:

- Document status validity (`CHECK` constraint)
- Single approval decision per document (`UNIQUE` constraint on `ApprovalStep.document`)
- Approval steps restricted to terminal states (`CHECK` constraint on `status` in `APPROVED`/`REJECTED`)

### 4.5 Concurrency & Idempotency Guarantees

- Workflow transitions are idempotent by design.
- Replayed transitions are rejected explicitly and produce no side effects.
- `select_for_update()` within a transaction ensures atomic decisions.

### 4.6 State Machine Guarantees

The state machine exposes a frozen `TransitionResult` contract:

- Pure evaluation only
- Explicit success/failure separation
- Stable, user-facing failure reasons
- No mutation or I/O
- On success, `reason` is `None`; on failure, `reason` is a stable explanation.

---

## 5. Approval Workflow Design

### Unified Approval Queue

There is **one approval queue** shared by Managers and Admins.

- Located at: `/documents/approvals/`
- Backed by `ApprovalQueueListView`
- Lists only `SUBMITTED` documents
- Excludes documents created by the current user

This avoids:

- Role fragmentation
- Approval deadlocks
- Manager/Admin duplication

---

## 6. Transactional Integrity

All approval decisions are wrapped in **database transactions**:

```python
with transaction.atomic():
    Document.objects.select_for_update().get(pk=document_id)
```

This guarantees:

- No double approvals
- No lost updates
- Correct audit ordering

---

## 7. Audit Architecture

### Audit Logging Strategy

- All workflow mutations (submit, approve, reject) are logged **exclusively** via `DocumentWorkflowService`.
- Document creation also logs an audit entry in the view (`DocumentCreateView`).
- Model signals are **only** used for post-migration group creation; they never enforce permissions or workflow rules.

### Audit Trail Principles

Every significant action produces an immutable audit log entry recording:

- Timestamp
- Action
- Actor
- Target document
- Optional metadata

### Audit Visibility

| View                         | Access               |
|------------------------------|----------------------|
| Per-document audit trail     | Admin only           |
| System-wide audit log list   | Admin only           |

Audit data is **read-only** and cannot be altered via the UI.

### Audit Presentation

- Audit action labels rendered via `get_action_display` in templates.
- Templates contain no conditional logic for audit actions.

---

## 8. Template Architecture

### Role Awareness

Templates do **not** query the database. Instead, role flags are injected via a **single context processor**:

```python
def role_flags(request):
    # Returns is_employee, is_manager, is_admin
```

This ensures:

- Consistent role logic
- Zero ORM usage in templates
- Predictable UI behavior

### Rich Text Editing

The system uses `django_summernote` for WYSIWYG editing of document content. The `DocumentForm` configures the Summernote widget with a custom toolbar.

---

## 9. URL and View Organization

Views are grouped by responsibility:

| Area                         | Responsibility     |
|------------------------------|--------------------|
| `document_list`              | Personal documents |
| `document_create` / `update` | Authoring          |
| `document_submit`            | State transition   |
| `document_decision`          | Approval decisions |
| `document_review_list`       | Approval queue     |
| `document_audit`             | Audit visibility   |

URLs are:

- Explicit
- Namespaced (`workflow` and `reports`)
- Non-overlapping

### Reports App

The `reports` app contains admin-only audit views:

- `AuditLogListView` – system-wide audit log with filtering
- `DocumentAuditLogView` – per-document audit trail

---

## 10. Observability Layer

The system includes a passive observability adapter inside the service layer. This layer:

- Emits structured logs
- Emits transition metrics
- Emits failure diagnostics
- Does **not** modify workflow behavior
- Does **not** participate in transactions
- Must never raise or swallow business exceptions

### Structured Logging

- Logs are formatted as JSON using a custom `JsonFormatter`.
- A `CorrelationIdMiddleware` injects a correlation ID into each request, which is included in all log records.
- Logging occurs at transition attempt, success, and controlled failure paths.

### Metrics

An in-process metrics collector (`WorkflowMetrics`) tracks:

- `workflow.transition.success` (counter)
- `workflow.transition.failure` (counter)
- `workflow.transition.latency_ms` (histogram)

Metrics are exposed via a staff-only endpoint at `/observability/metrics/` (JSON snapshot).

---

## 11. Security Posture Summary

The system enforces security through:

- Explicit permissions (no implicit trust)
- Defense-in-depth checks
- Transactional integrity
- Audit-first design
- No client-side authority assumptions

This architecture intentionally favors **clarity and correctness over convenience**.

---

## 12. Workflow Mutation Authority

All document lifecycle transitions (submit, approve, reject) are executed **exclusively** via `DocumentWorkflowService`.

Models, views, and signals are prohibited from mutating `Document.status`, creating `ApprovalStep`, or writing workflow-related `AuditLog` entries directly.

This guarantees:

- Exactly-once audit logging
- Centralized permission enforcement
- Transactional integrity

---
