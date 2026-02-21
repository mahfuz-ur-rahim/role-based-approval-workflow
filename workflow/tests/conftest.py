import pytest
from django.contrib.auth.models import User, Group
from workflow.models import Document


@pytest.fixture
def employee(db):
    user = User.objects.create_user(username="employee", password="pass")
    user.groups.add(Group.objects.get(name="Employee"))
    return user


@pytest.fixture
def manager(db):
    user = User.objects.create_user(username="manager", password="pass")
    user.groups.add(Group.objects.get(name="Manager"))
    return user


@pytest.fixture
def admin(db):
    user = User.objects.create_user(username="admin", password="pass")
    user.groups.add(Group.objects.get(name="Admin"))
    return user


@pytest.fixture
def draft_document(db, employee):
    return Document.objects.create(
        title="Draft Doc",
        content="content",
        created_by=employee,
    )


@pytest.fixture
def submitted_document(db, employee):
    doc = Document.objects.create(
        title="Submitted Doc",
        content="content",
        created_by=employee,
    )
    doc.submit(employee)
    return doc


@pytest.fixture
def client_logged_in(client):
    def _login(user):
        client.login(username=user.username, password="pass")
        return client
    return _login
