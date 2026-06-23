import pytest
from django.urls import reverse

from apps.core.models import User


@pytest.mark.django_db
def test_tree_count_report_pdf(client):
    user = User.objects.create_user(email="viewer@example.com", password="testpass123", role=User.Role.COMMITTEE_OFFICER)
    client.force_login(user)
    response = client.get(reverse("report-tree-count") + "?export=pdf")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
