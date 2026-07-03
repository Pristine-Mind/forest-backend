import pytest

from apps.core.services import (
    approve_harvest_request,
    process_membership_renewal,
    record_sale,
    record_visitor_entry,
    resolve_offense_fine_paid,
)
from apps.forest.models import TreeCountHistory, TreeCountRegister
from apps.harvest.models import HarvestRequest
from apps.inventory.models import Sale, StockLedger, StockTransaction
from apps.members.models import Member, MembershipRenewal


@pytest.mark.django_db
def test_approve_harvest_request_updates_tree_count_and_stock(harvest_request, tree_count, committee_user):
    result = approve_harvest_request(harvest_request, committee_user)

    assert result.status == HarvestRequest.Status.APPROVED

    tree_count.refresh_from_db()
    assert tree_count.harvested_count == 10
    assert tree_count.remaining_count == 90
    assert TreeCountHistory.objects.filter(record=tree_count).count() == 1

    ledger = StockLedger.objects.get(species=harvest_request.species, grade="A")
    assert ledger.quantity_available == 10
    assert StockTransaction.objects.filter(stock=ledger, transaction_type=StockTransaction.Type.IN).count() == 1


@pytest.mark.django_db
def test_approve_harvest_request_rollback_on_insufficient_stock(harvest_request, tree_count, committee_user):
    tree_count.total_count = 5
    tree_count.save()

    with pytest.raises(ValueError):
        approve_harvest_request(harvest_request, committee_user)

    harvest_request.refresh_from_db()
    assert harvest_request.status == HarvestRequest.Status.PENDING
    assert TreeCountHistory.objects.count() == 0
    assert StockLedger.objects.count() == 0


@pytest.mark.django_db
def test_record_sale_creates_sale_and_receipt_and_decrements_stock(tree_count, stock_ledger, price_rate, committee_user):
    # Seed stock
    from apps.core.services import approve_harvest_request
    from apps.harvest.models import HarvestRequest

    harvest = HarvestRequest.objects.create(
        source_type=HarvestRequest.SourceType.FOREST_INITIATED,
        operation_name="Thinning",
        species=stock_ledger.species,
        quantity=20,
        requested_date="2026-06-01",
    )
    approve_harvest_request(harvest, committee_user)

    sale_data = {
        "buyer_name": "Test Buyer",
        "buyer_type": Sale.BuyerType.MEMBER,
        "species": stock_ledger.species,
        "grade": "A",
        "quantity": 5,
    }

    sale = record_sale(sale_data, committee_user)

    assert sale.total_amount == 5000
    assert sale.receipt_no is not None
    stock_ledger.refresh_from_db()
    assert stock_ledger.quantity_available == 15


@pytest.mark.django_db
def test_record_sale_rollback_on_insufficient_stock(stock_ledger, committee_user):
    sale_data = {
        "buyer_name": "Test Buyer",
        "buyer_type": Sale.BuyerType.MEMBER,
        "species": stock_ledger.species,
        "grade": "A",
        "quantity": 5,
    }

    with pytest.raises(ValueError):
        record_sale(sale_data, committee_user)

    assert Sale.objects.count() == 0


@pytest.mark.django_db
def test_process_membership_renewal_creates_renewal_and_receipt(member, committee_user, system_config):
    renewal = process_membership_renewal(member, "2082/83", "2026-06-15", committee_user)

    assert renewal is not None
    assert renewal.fee_charged == system_config.renewal_fee_on_time
    assert MembershipRenewal.objects.filter(member=member).count() == 1


@pytest.mark.django_db
def test_process_membership_renewal_cancels_after_threshold(member, committee_user, system_config):
    MembershipRenewal.objects.create(
        member=member,
        fiscal_year="2077/78",
        fee_tier=MembershipRenewal.FeeTier.ON_TIME,
        fee_charged=50,
        paid_date="2021-01-01",
    )

    result = process_membership_renewal(member, "2083/84", "2026-06-15", committee_user)

    assert result is None
    member.refresh_from_db()
    assert member.membership_status == Member.MembershipStatus.CANCELLED


@pytest.mark.django_db
def test_record_visitor_entry_creates_receipt_and_fee_collection_when_not_waived(committee_user, visitor_fee_rate):
    from apps.billing.models import FeeCollection
    from apps.visitors.models import VisitorEntry

    entry = record_visitor_entry(
        {
            "entry_date": "2026-06-15",
            "visit_purpose": VisitorEntry.VisitPurpose.GENERAL_VISIT,
            "visitor_count": 5,
            "days": 2,
            "fee_waived": False,
        },
        committee_user,
    )

    assert entry.receipt_no is not None
    assert entry.total_amount > 0
    assert FeeCollection.objects.filter(
        fee_type=FeeCollection.FeeType.VISITOR_ENTRY,
        amount=entry.total_amount,
        amount_paid=entry.total_amount,
        receipt_no=entry.receipt_no,
    ).exists()


@pytest.mark.django_db
def test_resolve_offense_fine_paid_requires_fee_collection(member, committee_user):
    from apps.offense.models import HearingRecord, OffenseReport

    offense = OffenseReport.objects.create(
        accused_name="Accused",
        offense_type="Illegal logging",
        description="Cut trees without permission",
        report_date="2026-06-01",
        fine_amount=5000,
        informant=member,
    )
    HearingRecord.objects.create(
        offense=offense,
        accused_statement="I admit",
        hearing_date="2026-06-10",
        outcome=HearingRecord.Outcome.ADMITTED,
    )

    with pytest.raises(ValueError):
        resolve_offense_fine_paid(offense, member.pk, committee_user)


@pytest.mark.django_db
def test_resolve_offense_fine_paid_creates_reward(member, committee_user):
    from apps.billing.models import FeeCollection
    from apps.offense.models import HearingRecord, OffenseReport

    offense = OffenseReport.objects.create(
        accused_name="Accused",
        offense_type="Illegal logging",
        description="Cut trees without permission",
        report_date="2026-06-01",
        fine_amount=5000,
        informant=member,
    )
    HearingRecord.objects.create(
        offense=offense,
        accused_statement="I admit",
        hearing_date="2026-06-10",
        outcome=HearingRecord.Outcome.ADMITTED,
    )
    FeeCollection.objects.create(
        member=member,
        fee_type=FeeCollection.FeeType.OTHER,
        amount=5000,
        amount_paid=5000,
        description=f"Fine for offense #{offense.pk}",
    )

    resolve_offense_fine_paid(offense, member.pk, committee_user)

    offense.refresh_from_db()
    assert offense.status == OffenseReport.Status.RESOLVED
    assert offense.reward.reward_amount == 500
