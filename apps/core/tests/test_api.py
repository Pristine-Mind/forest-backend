import pytest
from django.urls import reverse

from apps.core.models import User


@pytest.mark.django_db
def test_me_endpoint(client):
    user = User.objects.create_user(email="test@example.com", password="testpass123")
    client.force_login(user)
    response = client.get(reverse("user-me"))
    assert response.status_code == 200
    assert response.json()["email"] == user.email
