# Role-Based Document Approval Workflow

A Django-based role-driven document approval system.

## Features
- Draft → Submitted → Approved / Rejected
- Employee / Manager / Admin roles
- Role-based login redirect
- Manager approval interface
- Secure access control

## Tech Stack
- Python 3.11
- Django 5.x
- SQLite (dev)

## Setup Instructions
```bash
git clone https://github.com/YOUR_USERNAME/role-based-approval-workflow.git
cd role-based-approval-workflow
```
### Option A — Pipenv (recommended)
Install `pipenv` if not installed
```bash
cd role-based-approval-workflow
pip install pipenv
```

```bash
pipenv install
pipenv shell
python manage.py migrate
python manage.py runserver
```
### Option B — requirements.txt
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
## Login at:
```
http://localhost:8000/accounts/login/
```
