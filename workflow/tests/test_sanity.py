import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_employee_can_see_document_list(client_logged_in, employee):
    client = client_logged_in(employee)
    resp = client.get(reverse("workflow:document-list"))
    assert resp.status_code == 200
