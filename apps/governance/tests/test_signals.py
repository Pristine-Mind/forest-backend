import pytest
from django.urls import reverse

from apps.core.models import User
from apps.governance.models import CommitteeMember, HandoverRecord
from apps.members.models import Household, Member


@pytest.mark.django_db
def test_handover_record_created_on_committee_member_removal(client, committee_user):
    household = Household.objects.create(
        household_head_name="Head",
        wealth_class=Household.WealthClass.POOR,
        registration_date="2020-01-01",
    )
    member = Member.objects.create(
        household=household,
        full_name="Committee Member",
        citizenship_no="CIT-GOV-001",
        date_joined="2020-01-01",
    )
    cm = CommitteeMember.objects.create(
        member=member,
        position=CommitteeMember.Position.MEMBER,
        gender="male",
        term_start="2026-01-01",
        term_end="2028-12-31",
        status=CommitteeMember.Status.ACTIVE,
    )

    assert HandoverRecord.objects.count() == 0

    cm.status = CommitteeMember.Status.REMOVED
    cm.save()

    assert HandoverRecord.objects.filter(outgoing_committee_member=cm).count() == 1


@pytest.mark.django_db
def test_quota_status_endpoint(client, committee_user):
    household = Household.objects.create(
        household_head_name="Head",
        wealth_class=Household.WealthClass.POOR,
        registration_date="2020-01-01",
    )
    member = Member.objects.create(
        household=household,
        full_name="Female Member",
        citizenship_no="CIT-GOV-002",
        date_joined="2020-01-01",
    )
    CommitteeMember.objects.create(
        member=member,
        position=CommitteeMember.Position.MEMBER,
        gender="female",
        caste_ethnicity="Dalit",
        term_start="2026-01-01",
        term_end="2028-12-31",
        status=CommitteeMember.Status.ACTIVE,
    )

    client.force_login(committee_user)
    response = client.get(reverse("committeemember-quota-status"))
    assert response.status_code == 200
    data = response.json()
    assert data["total_active"] == 1
    assert data["female_count"] == 1
