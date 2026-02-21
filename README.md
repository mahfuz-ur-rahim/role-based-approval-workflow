# Role-Based Approval Workflow (RBAW)

A Django-based document approval system implementing a role-driven state machine workflow with structured audit logging and deterministic concurrency controls.

## Features

- Role-based access control (Employee, Manager, Admin)
- Document lifecycle: DRAFT → SUBMITTED → APPROVED / REJECTED
- Transactional state transitions and DB constraints to prevent duplicate decisions
- Immutable audit logging of all state mutations
- Structured JSON logging with request correlation IDs
- Bootstrap 4 UI and Django admin for operations

## Technology Stack

- Python 3.11+
- Django 5.2
- PostgreSQL
- Bootstrap 4 (frontend)
- django-summernote (rich text editor)
- Pytest + pytest-django (testing)

## Quick Start

1. Clone the repo

```bash
   git clone https://github.com/mahfuz-ur-rahim/role-based-approval-workflow.git
   cd role-based-approval-workflow
```

2. Create & activate a virtual environment

```bash
   python -m venv .venv
   source .venv/bin/activate
```

3. Install dependencies

```bash
   pip install -r requirements.txt
```

4. Configure PostgreSQL

   - Create database and user matching `rbaw_project/settings.py` or update settings:
     - NAME: `rbaw_dev`
     - USER: `rbaw_user`
     - PASSWORD: `strongpassword`
     - HOST: `localhost`
     - PORT: `5432`

5. Run migrations

   python manage.py migrate

   The app registers a post-migrate signal to create default groups (`Employee`, `Manager`, `Admin`) automatically (see [`workflow.signals.create_default_groups`](workflow/signals.py)).

6. Create a superuser

```bash
   python manage.py createsuperuser
```

7. Run the development server

```bash
   python manage.py runserver
```

8. Visit:

   <http://127.0.0.1:8000/> — main app
   <http://127.0.0.1:8000/admin/> — Django admin

## Roles & Capabilities

- Employee
  - Create documents (DRAFT)
  - Edit own drafts
  - Submit own drafts for approval
  - View own documents and audit for owned documents

- Manager
  - All Employee permissions
  - Approve or reject submitted documents (not their own)

- Admin
  - Full visibility (can view audit logs and all documents)
  - Can act as approver (Admin group members)

Domain-level enforcement is implemented inside the model methods (see [`workflow.models.document.Document`](workflow/models/document.py)) — e.g. [`Document.submit`](workflow/models/document.py), [`Document.approve`](workflow/models/document.py), and [`Document.reject`](workflow/models/document.py).

## Running Tests

Run the test suite with pytest:

```bash
pytest
```

Tests include concurrency and permission boundary checks located under `workflow/tests/`.

## Important Files / Entry Points

- Project settings: [rbaw_project/settings.py](rbaw_project/settings.py)
- Manage CLI: [manage.py](manage.py)
- Document domain: [`workflow/models/document.py`](workflow/models/document.py)
- Audit model: [`workflow/models/audit.py`](workflow/models/audit.py)
- Approval step & DB constraints: [`workflow/models/approval.py`](workflow/models/approval.py)
- Default groups signal: [`workflow/signals.py`](workflow/signals.py)
- Views / URLs: [`workflow/urls.py`](workflow/urls.py) and `workflow/views/`
- Requirements: [requirements.txt](requirements.txt)

## Notes

- Default groups are created by the `post_migrate` signal; ensure migrations are run once to populate groups.
- The app enforces permissions at both view and model layers (defense-in-depth).
- Structured logging and correlation IDs are provided by `workflow/logging.py` and `workflow/middleware.py`.

Happy developing.
