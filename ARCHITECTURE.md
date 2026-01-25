# Architecture Overview

## Role-Based Document Approval Workflow System

## 1. Architectural Goals

This system is designed to demonstrate a **secure, auditable, role-based approval workflow** with explicit enforcement of separation of duties. The architecture prioritizes:

* Clear responsibility boundaries between roles
* Explicit workflow state transitions
* Auditability of all sensitive actions
* Defense-in-depth (UI, view, and data-layer checks)
* Educational clarity over framework “magic”

---

## 2. Core Domain Model

### Document Lifecycle

Documents move through a **strict, linear lifecycle**:

```txt
DRAFT → SUBMITTED → APPROVED / REJECTED
```

Transitions are:

* Explicit
* Atomic
* Audited
* Permission-checked

No implicit state changes exist.

---

## 3. Roles and Responsibilities

Roles are implemented using **Django Groups**.

| Role     | Capabilities                                            |
| -------- | ------------------------------------------------------- |
| Employee | Create, edit (draft), submit documents                  |
| Manager  | All Employee actions + approve/reject others’ documents |
| Admin    | All Manager actions + system-wide audit visibility      |

### Important Rules

* **Admins are approvers**, not automatic approvers
* **No role can approve its own documents**
* Superusers bypass group checks but are still blocked from self-approval

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

* `EmployeeRequiredMixin`
* `ManagerRequiredMixin`
* `AdminRequiredMixin`
* `ApproverRequiredMixin`

#### ApproverRequiredMixin

Allows access to approval actions for:

* Managers
* Admins

Self-approval is **explicitly forbidden at the view level**, not in the mixin.

---

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

* UI bypasses are ineffective
* Concurrent approval attempts are safe
* Integrity is preserved under race conditions

---

> #### Authorization & Error Semantics
>
> * Authorization failures (role violations, self-approval) raise `PermissionDenied` (403)
> * Resource absence raises `Http404`
> * Views enforce authorization; templates remain passive
> * Tests assert HTTP semantics explicitly

---

## 5. Approval Workflow Design

### Unified Approval Queue

There is **one approval queue** shared by Managers and Admins.

* Located at: `/documents/approvals/`
* Backed by `ApprovalQueueListView`
* Lists only `SUBMITTED` documents
* Excludes documents created by the current user

This avoids:

* Role fragmentation
* Approval deadlocks
* Manager/Admin duplication

---

## 6. Transactional Integrity

All approval decisions are wrapped in **database transactions**:

```python
with transaction.atomic():
    Document.objects.select_for_update()
```

This guarantees:

* No double approvals
* No lost updates
* Correct audit ordering

---

## 7. Audit Architecture

### Audit Logging Strategy

* Authorization-bound actions (approve/reject) log audits at the view/service layer
* Model signals may be used for creation-time logging only
* Signals must never enforce permissions or workflow rules

### Audit Trail Principles

Every significant action:

* Submission
* Approval
* Rejection

Produces an immutable audit log entry.

Audit logs record:

* Timestamp
* Action
* Actor
* Target document
* Optional metadata

### Audit Visibility

| View                   | Access |
| ---------------------- | ------ |
| Per-document audit     | Admin  |
| System-wide audit list | Admin  |

Audit data is **read-only** and cannot be altered via the UI.

---

## 8. Template Architecture

### Role Awareness

Templates do **not** query the database.

Instead, role flags are injected via a **single context processor**:

```python
role_flags(request)
```

Provides:

* `is_employee`
* `is_manager`
* `is_admin`

This ensures:

* Consistent role logic
* Zero ORM usage in templates
* Predictable UI behavior

---

## 9. URL and View Organization

Views are grouped by responsibility:

| Area                     | Responsibility     |
| ------------------------ | ------------------ |
| document_list            | Personal documents |
| document_create / update | Authoring          |
| document_submit          | State transition   |
| document_decision        | Approval decisions |
| document_review_list     | Approval queue     |
| document_audit           | Audit visibility   |

URLs are:

* Explicit
* Namespaced
* Non-overlapping

No legacy Manager-only approval paths remain.

---

## 10. Security Posture Summary

The system enforces security through:

* Explicit permissions (no implicit trust)
* Defense-in-depth checks
* Transactional integrity
* Audit-first design
* No client-side authority assumptions

This architecture intentionally favors **clarity and correctness over convenience**.

---

## 11. Architecture Status

### Phase 4 Architecture: FROZEN

* Core behavior finalized
* No further structural changes planned
* Future phases may add reporting or analytics **without altering core workflow**

### User Feedback & Messaging

* Messages framework used for success only
* Authorization failures handled exclusively by 403/404
* No business rules exposed in UI feedback

### Audit Log Presentation & Visibility

* Raw audit data preserved
* Presentation varies by context (global vs document)
* Admins have full visibility; others scoped
* UX does not alter enforcement
