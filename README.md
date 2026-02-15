# Role-Based Approval Workflow System

A Django-based document approval system implementing a **role-driven state machine workflow** with structured logging, metrics, and audit visibility.

The project demonstrates:

- Clean service-layer architecture

- Explicit workflow state machine

- Role-based authorization via Django Groups

- Structured observability (logs + metrics)

- Transaction-safe state transitions

----------

## Overview

This system manages a simple document lifecycle:

```text
DRAFT → SUBMITTED → APPROVED / REJECTED
```

Access and transitions are controlled by roles:

Role

Capabilities

Employee

Create & submit own documents

Manager

Approve / Reject submitted documents

Admin

Full visibility

All state mutations are executed through a **single service authority** to ensure:

- No illegal transitions

- No duplicate transitions

- No unauthorized approvals

- Full audit logging

- Structured observability

----------

## Tech Stack

- **Python 3.11+**

- **Django 5.2**

- **PostgreSQL** (recommended, SQLite works for dev)

- **Pytest + pytest-django**

- Built-in Django Groups for RBAC

----------

## Core Concepts

### 1. Service Layer

All state changes go through:

```python
DocumentWorkflowService

```

No view directly mutates document state.

----------

### 2. State Machine

Transitions are evaluated via:

```python
evaluate_transition(...)

```

Failure types:

- `INVALID_STATE`

- `PERMISSION`

- `IDEMPOTENT_REPLAY`

----------

### 3. Observability

Includes:

- Structured logging

- Transition attempt/result events

- In-memory metrics adapter

- Admin-only metrics endpoint

----------

## Project Structure (High Level)

```text
workflow/
│
├── models/
│   ├── document.py
│   ├── approval.py
│   └── audit.py
│
├── services/
│   └── document_workflow.py
│
├── state_machine.py
├── observability.py
├── metrics.py
│
├── views/        # Module-based views
├── templates/
└── tests/
```

The service layer is the authoritative boundary for business rules.

----------

## Installation Guide

### 1. Clone Repository

```bash
git clone https://github.com/mahfuz-ur-rahim/role-based-approval-workflow.git
cd role-based-approval-workflow
```

----------

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux / macOS

```

----------

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

----------

### 4. Configure Environment

Create a `.env` file or configure database settings inside `settings.py`.

For quick local setup, SQLite works out of the box.

----------

### 5. Run Migrations

```bash
python manage.py migrate
```

----------

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

----------

### 7. Create Roles (Once)

Inside Django admin:

- Create Groups:

  - `Employee`

  - `Manager`

  - `Admin`

Assign users to appropriate groups.

----------

### 8. Run Server

```bash
python manage.py runserver
```

Visit:

```bash
http://127.0.0.1:8000/
```

----------

## Running Tests

```bash
pytest
```

All tests should pass before merging changes.

----------

## Manual Testing Flow

1. Login as Employee

2. Create document (status: DRAFT)

3. Submit document (status: SUBMITTED)

4. Login as Manager

5. Approve or Reject

Verify:

- Illegal transitions are blocked

- Permission violations raise 403

- Audit logs are created

- Structured logs appear in console

- Metrics endpoint returns JSON

----------

## Observability Endpoints

Admin-only:

```text
/workflow/metrics/
```

Returns JSON snapshot:

```json
{
  "service": "workflow",
  "metrics": {
    "counters": {},
    "latencies": {}
  }
}
```

----------

## Design Principles

- Single mutation authority

- Explicit failure types

- Transactional consistency

- Idempotency protection

- Production-oriented logging

- Test-first verification

----------

## Purpose

This project demonstrates how to structure a **production-ready workflow system** with:

- Strong separation of concerns

- Deterministic state transitions

- Observable runtime behavior

- Clean service-layer architecture

----------
