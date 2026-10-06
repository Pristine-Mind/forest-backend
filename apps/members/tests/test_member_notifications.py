import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import Notification, User
from apps.members.models import Household


@pytest.mark.django_db
def test_staff_household_creation_notifies_committee_chairs():
    staff = User.objects.create_user(
        email="staff@example.com",
        password="testpass123",
        role=User.Role.STAFF,
    )
    chair = User.objects.create_user(
        email="chair@example.com",
        password="testpass123",
        role=User.Role.COMMITTEE_CHAIR,
    )
    client = APIClient()
    client.force_authenticate(user=staff)

    response = client.post(
        reverse("household-list"),
        {
            "household_head_name": "Household Head",
            "wealth_class": Household.WealthClass.MEDIUM,
            "registration_date": "2020-01-01",
        },
        format="json",
    )

    assert response.status_code == 201
    household = Household.objects.get(pk=response.data["id"])
    notification = Notification.objects.get(recipient=chair)
    assert notification.notification_type == Notification.Type.MEMBER_REQUEST
    assert notification.title == "New Member Request: Household Head"
    assert "staff@example.com requested to add a new member" in notification.description
    assert notification.action_required is True
    assert notification.content_type == "Household"
    assert notification.object_id == household.pk
    assert notification.created_by == staff
    assert household.approval_status == Household.ApprovalStatus.PENDING


@pytest.mark.django_db
def test_staff_household_creation_succeeds_without_committee_chairs():
    staff = User.objects.create_user(
        email="staff@example.com",
        password="testpass123",
        role=User.Role.STAFF,
    )
    client = APIClient()
    client.force_authenticate(user=staff)

    response = client.post(
        reverse("household-list"),
        {
            "household_head_name": "Household Head",
            "wealth_class": Household.WealthClass.MEDIUM,
            "registration_date": "2020-01-01",
        },
        format="json",
    )

    assert response.status_code == 201
    assert Household.objects.filter(pk=response.data["id"]).exists()
    assert response.data["approval_status"] == Household.ApprovalStatus.PENDING
    assert not Notification.objects.exists()


@pytest.mark.django_db
def test_chair_can_approve_household_request_and_action_notification():
    staff = User.objects.create_user(
        email="staff@example.com",
        password="testpass123",
        role=User.Role.STAFF,
    )
    chair = User.objects.create_user(
        email="chair@example.com",
        password="testpass123",
        role=User.Role.COMMITTEE_CHAIR,
    )
    client = APIClient()
    client.force_authenticate(user=staff)
    created = client.post(
        reverse("household-list"),
        {
            "household_head_name": "Household Head",
            "wealth_class": Household.WealthClass.MEDIUM,
            "registration_date": "2020-01-01",
        },
        format="json",
    )
    household_id = created.data["id"]

    client.force_authenticate(user=chair)
    response = client.post(reverse("household-approve", args=[household_id]), format="json")

    assert response.status_code == 200
    household = Household.objects.get(pk=household_id)
    assert household.approval_status == Household.ApprovalStatus.APPROVED
    assert household.approved_by == chair
    assert household.approved_at is not None
    notification = Notification.objects.get(recipient=chair)
    assert notification.status == Notification.Status.ACTIONED
    assert notification.actioned_by == chair
    assert notification.action_notes == "Household request accepted."


@pytest.mark.django_db
def test_chair_can_reject_household_request_with_reason():
    staff = User.objects.create_user(
        email="staff@example.com",
        password="testpass123",
        role=User.Role.STAFF,
    )
    chair = User.objects.create_user(
        email="chair@example.com",
        password="testpass123",
        role=User.Role.COMMITTEE_CHAIR,
    )
    client = APIClient()
    client.force_authenticate(user=staff)
    created = client.post(
        reverse("household-list"),
        {
            "household_head_name": "Household Head",
            "wealth_class": Household.WealthClass.MEDIUM,
            "registration_date": "2020-01-01",
        },
        format="json",
    )
    household_id = created.data["id"]

    client.force_authenticate(user=chair)
    response = client.post(
        reverse("household-reject", args=[household_id]),
        {"rejection_reason": "Missing supporting documents"},
        format="json",
    )

    assert response.status_code == 200
    household = Household.objects.get(pk=household_id)
    assert household.approval_status == Household.ApprovalStatus.REJECTED
    assert household.rejection_reason == "Missing supporting documents"
    notification = Notification.objects.get(recipient=chair)
    assert notification.status == Notification.Status.ACTIONED
    assert notification.actioned_by == chair
    assert notification.action_notes == "Household request rejected: Missing supporting documents"
