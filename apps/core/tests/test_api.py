import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token

from apps.core.models import User


@pytest.mark.django_db
def test_me_endpoint(client):
    user = User.objects.create_user(email="test@example.com", password="testpass123")
    client.force_login(user)
    response = client.get(reverse("user-me"))
    assert response.status_code == 200
    assert response.json()["email"] == user.email


@pytest.mark.django_db
def test_login_success(client):
    user = User.objects.create_user(email="login@example.com", password="testpass123")
    response = client.post(
        reverse("auth-login"),
        data={"email": "login@example.com", "password": "testpass123"},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == user.email
    assert Token.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_login_invalid_credentials(client):
    User.objects.create_user(email="login@example.com", password="testpass123")
    response = client.post(
        reverse("auth-login"),
        data={"email": "login@example.com", "password": "wrongpassword"},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_missing_fields(client):
    response = client.post(
        reverse("auth-login"),
        data={"email": "login@example.com"},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_logout_success(client):
    user = User.objects.create_user(email="logout@example.com", password="testpass123")
    token = Token.objects.create(user=user)
    response = client.post(
        reverse("auth-logout"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    assert response.status_code == 200
    assert not Token.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_logout_unauthenticated(client):
    response = client.post(reverse("auth-logout"), content_type="application/json")
    assert response.status_code == 401
