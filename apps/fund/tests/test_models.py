import pytest

from apps.core.models import SystemConfig
from apps.fund.models import Audit, CashTransaction


@pytest.mark.django_db
def test_cash_transaction_flags_committee_approval():
    config = SystemConfig.get()
    tx = CashTransaction.objects.create(
        type=CashTransaction.Type.INCOME,
        source_or_purpose="Membership fee",
        amount=config.cash_chair_approval_limit + 1,
    )
    assert tx.requires_committee_approval is True

    tx_small = CashTransaction.objects.create(
        type=CashTransaction.Type.INCOME,
        source_or_purpose="Small donation",
        amount=100,
    )
    assert tx_small.requires_committee_approval is False


@pytest.mark.django_db
def test_audit_tier_computed_from_total_income():
    config = SystemConfig.get()
    internal = Audit.objects.create(
        fiscal_year="2082/83",
        total_income=config.audit_external_threshold - 1,
        auditor_name="Internal Auditor",
    )
    assert internal.audit_tier == Audit.Tier.INTERNAL

    external = Audit.objects.create(
        fiscal_year="2082/83",
        total_income=config.audit_external_threshold + 1,
        auditor_name="External Auditor",
    )
    assert external.audit_tier == Audit.Tier.EXTERNAL
