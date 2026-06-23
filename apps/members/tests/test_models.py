import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.livelihood.models import LivelihoodProgramRecord, RevolvingFundLoan
from apps.members.models import Household, Member


@pytest.mark.django_db
def test_citizenship_number_unique():
    household = Household.objects.create(
        household_head_name="H1",
        wealth_class=Household.WealthClass.POOR,
        registration_date="2020-01-01",
    )
    Member.objects.create(
        household=household,
        full_name="M1",
        citizenship_no="CIT-001",
        date_joined="2020-01-01",
    )
    with pytest.raises(IntegrityError):
        Member.objects.create(
            household=household,
            full_name="M2",
            citizenship_no="CIT-001",
            date_joined="2020-01-01",
        )


@pytest.mark.django_db
def test_revolving_fund_loan_requires_poor_household():
    rich_household = Household.objects.create(
        household_head_name="Rich",
        wealth_class=Household.WealthClass.RICH,
        registration_date="2020-01-01",
    )
    with pytest.raises(ValidationError):
        RevolvingFundLoan.objects.create(
            household=rich_household,
            amount=1000,
            issue_date="2026-01-01",
        )


@pytest.mark.django_db
def test_livelihood_program_requires_poor_household():
    medium_household = Household.objects.create(
        household_head_name="Medium",
        wealth_class=Household.WealthClass.MEDIUM,
        registration_date="2020-01-01",
    )
    with pytest.raises(ValidationError):
        LivelihoodProgramRecord.objects.create(
            household=medium_household,
            program_type=LivelihoodProgramRecord.ProgramType.LIVESTOCK,
            amount_or_value=500,
            program_date="2026-01-01",
        )
