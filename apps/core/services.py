from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import transaction

from apps.core.models import AuditLog, SystemConfig


def _schedule_receipt_pdf(receipt_no: str):
    """Queue receipt PDF generation after the current transaction commits."""

    from apps.billing.tasks import generate_receipt_pdf_task

    transaction.on_commit(lambda: generate_receipt_pdf_task.delay(receipt_no))


def log_audit(
    action: AuditLog.Action,
    model_name: str,
    object_id: str | int | None = None,
    old_value: str = "",
    new_value: str = "",
    reason: str = "",
    user=None,
):
    """Create an audit log entry."""

    return AuditLog.objects.create(
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id is not None else "",
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        **({"created_by": user, "updated_by": user} if user else {}),
    )


@transaction.atomic
def approve_harvest_request(harvest_request, approved_by_user):
    """
    Atomic harvest approval workflow.
    Updates harvest request, tree count register, tree count history, and stock.
    """

    from apps.forest.models import TreeCountHistory, TreeCountRegister
    from apps.harvest.models import HarvestRequest
    from apps.inventory.models import StockLedger, StockTransaction

    if harvest_request.status != HarvestRequest.Status.PENDING:
        raise ValueError("Only pending harvest requests can be approved.")

    grade = "A"

    tree_count = TreeCountRegister.objects.select_for_update().get(species=harvest_request.species)

    if harvest_request.quantity > tree_count.remaining_count:
        raise ValueError(
            f"Requested quantity ({harvest_request.quantity}) exceeds remaining count "
            f"({tree_count.remaining_count}) for {harvest_request.species}."
        )

    harvest_request.status = HarvestRequest.Status.APPROVED
    harvest_request.approved_by = approved_by_user
    harvest_request.save(user=approved_by_user)

    old_harvested = tree_count.harvested_count
    tree_count.harvested_count += int(harvest_request.quantity)
    tree_count.save(user=approved_by_user)

    TreeCountHistory.objects.create(
        record=tree_count,
        change_amount=int(harvest_request.quantity),
        reference_harvest=harvest_request,
        change_date=date.today(),
        note=f"Approved harvest request #{harvest_request.pk}",
        created_by=approved_by_user,
        updated_by=approved_by_user,
    )

    stock_ledger, _ = StockLedger.objects.select_for_update().get_or_create(
        species=harvest_request.species,
        grade=grade,
        defaults={"created_by": approved_by_user, "updated_by": approved_by_user},
    )
    StockTransaction.objects.create(
        stock=stock_ledger,
        transaction_type=StockTransaction.Type.IN,
        quantity=harvest_request.quantity,
        reference_type=StockTransaction.ReferenceType.HARVEST,
        reference_id=harvest_request.pk,
        note=f"From approved harvest request #{harvest_request.pk}",
        created_by=approved_by_user,
        updated_by=approved_by_user,
    )

    log_audit(
        action=AuditLog.Action.HARVEST_APPROVAL,
        model_name="HarvestRequest",
        object_id=harvest_request.pk,
        old_value=str(old_harvested),
        new_value=str(tree_count.harvested_count),
        reason=f"Approved by {approved_by_user.email}",
        user=approved_by_user,
    )

    return harvest_request


@transaction.atomic
def record_sale(sale_data, issued_by_user):
    """
    Atomic sale recording workflow.
    Validates stock, looks up price, creates sale, stock transaction, and receipt.
    """

    from apps.billing.models import Receipt
    from apps.inventory.models import PriceRate, Sale, StockLedger, StockTransaction

    species = sale_data["species"]
    grade = sale_data["grade"]
    buyer_type = sale_data["buyer_type"]
    quantity = sale_data["quantity"]

    stock_ledger = StockLedger.objects.select_for_update().get(species=species, grade=grade)

    if quantity > stock_ledger.quantity_available:
        raise ValueError(
            f"Requested quantity ({quantity}) exceeds available stock "
            f"({stock_ledger.quantity_available}) for {species} grade {grade}."
        )

    rate = (
        PriceRate.objects.filter(species=species, grade=grade, buyer_type=buyer_type, effective_from__lte=date.today())
        .order_by("-effective_from")
        .first()
    )

    rate_applied = sale_data.get("rate_applied")
    audit_note = sale_data.get("audit_note", "")
    if rate_applied is None:
        if rate is None:
            raise ValueError(f"No price rate found for {species} grade {grade} buyer type {buyer_type}.")
        rate_applied = rate.rate_per_unit
    else:
        if not audit_note:
            raise ValueError("Audit note is required when manually editing the applied rate.")

    total_amount = Decimal(quantity) * Decimal(rate_applied)

    receipt = Receipt.objects.create(
        reference_type=Receipt.ReferenceType.SALE,
        reference_id=0,
        amount=total_amount,
        issued_date=date.today(),
        issued_by=issued_by_user,
        created_by=issued_by_user,
        updated_by=issued_by_user,
    )

    sale = Sale.objects.create(
        buyer_name=sale_data["buyer_name"],
        buyer_type=buyer_type,
        member=sale_data.get("member"),
        species=species,
        grade=grade,
        quantity=quantity,
        rate_applied=rate_applied,
        total_amount=total_amount,
        payment_status=sale_data.get("payment_status", Sale.PaymentStatus.DUE),
        receipt_no=receipt,
        audit_note=audit_note,
        created_by=issued_by_user,
        updated_by=issued_by_user,
    )

    receipt.reference_id = sale.pk
    receipt.save(update_fields=["reference_id"], user=issued_by_user)
    _schedule_receipt_pdf(receipt.receipt_no)

    StockTransaction.objects.create(
        stock=stock_ledger,
        transaction_type=StockTransaction.Type.OUT,
        quantity=quantity,
        reference_type=StockTransaction.ReferenceType.SALE,
        reference_id=sale.pk,
        note=f"Sale #{sale.pk}",
        created_by=issued_by_user,
        updated_by=issued_by_user,
    )

    log_audit(
        action=AuditLog.Action.SALE_RECORDED,
        model_name="Sale",
        object_id=sale.pk,
        new_value=str(total_amount),
        reason=f"Recorded by {issued_by_user.email}",
        user=issued_by_user,
    )

    return sale


@transaction.atomic
def process_membership_renewal(member, fiscal_year, paid_date, issued_by_user):
    """
    Atomic membership renewal workflow.
    Computes fee tier, creates renewal + fee collection + receipt.
    Cancels membership if elapsed years exceed the configured threshold.
    """

    from apps.billing.models import FeeCollection, Receipt
    from apps.members.models import Member, MembershipRenewal

    config = SystemConfig.get()

    last_renewal = member.last_renewal()
    if last_renewal is None:
        years = 0
    else:
        try:
            last_year = int(last_renewal.fiscal_year.split("/")[0])
            current_year = int(fiscal_year.split("/")[0])
            years = max(0, current_year - last_year)
        except (ValueError, IndexError):
            years = 1

    if years > config.membership_cancellation_years:
        old_status = member.membership_status
        member.membership_status = Member.MembershipStatus.CANCELLED
        member.save(user=issued_by_user)
        log_audit(
            action=AuditLog.Action.MEMBERSHIP_CANCELLATION,
            model_name="Member",
            object_id=member.pk,
            old_value=old_status,
            new_value=member.membership_status,
            reason=f"Unrenewed for {years} years",
            user=issued_by_user,
        )
        return None

    fee_tier = member.fee_tier_for_year(fiscal_year)
    fee_charged = member.renewal_fee_for_tier(fee_tier)

    renewal = MembershipRenewal.objects.create(
        member=member,
        fiscal_year=fiscal_year,
        fee_tier=fee_tier,
        fee_charged=fee_charged,
        paid_date=paid_date,
        created_by=issued_by_user,
        updated_by=issued_by_user,
    )

    receipt = Receipt.objects.create(
        reference_type=Receipt.ReferenceType.FEE_COLLECTION,
        reference_id=0,
        amount=fee_charged,
        issued_date=paid_date,
        issued_by=issued_by_user,
        created_by=issued_by_user,
        updated_by=issued_by_user,
    )

    fee_collection = FeeCollection.objects.create(
        member=member,
        fee_type=FeeCollection.FeeType.RENEWAL,
        amount=fee_charged,
        amount_paid=fee_charged,
        receipt_no=receipt,
        description=f"Membership renewal for fiscal year {fiscal_year}",
        created_by=issued_by_user,
        updated_by=issued_by_user,
    )

    receipt.reference_id = fee_collection.pk
    receipt.save(update_fields=["reference_id"], user=issued_by_user)
    _schedule_receipt_pdf(receipt.receipt_no)

    return renewal


@transaction.atomic
def record_visitor_entry(entry_data, issued_by_user):
    """Atomic visitor entry logging: creates entry and receipt if not waived."""

    from apps.billing.models import Receipt
    from apps.visitors.models import VisitorEntry

    entry = VisitorEntry.objects.create(
        entry_date=entry_data["entry_date"],
        visit_purpose=entry_data["visit_purpose"],
        visitor_count=entry_data["visitor_count"],
        days=entry_data["days"],
        fee_waived=entry_data.get("fee_waived", False),
        created_by=issued_by_user,
        updated_by=issued_by_user,
    )

    if not entry.fee_waived and entry.total_amount > 0:
        receipt = Receipt.objects.create(
            reference_type=Receipt.ReferenceType.VISITOR_ENTRY,
            reference_id=entry.pk,
            amount=entry.total_amount,
            issued_date=entry.entry_date,
            issued_by=issued_by_user,
            created_by=issued_by_user,
            updated_by=issued_by_user,
        )
        entry.receipt_no = receipt
        entry.save(update_fields=["receipt_no"], user=issued_by_user)
        _schedule_receipt_pdf(receipt.receipt_no)

    return entry


@transaction.atomic
def resolve_offense_fine_paid(offense, informant_id, resolved_by_user, resolution=None):
    """
    Atomic offense resolution workflow.
    Ensures fee collection exists for fines, then sets resolution and creates
    informant reward when applicable.
    """

    from apps.billing.models import FeeCollection
    from apps.offense.models import InformantReward, OffenseReport

    if resolution is None:
        resolution = OffenseReport.Resolution.FINE_PAID

    if resolution not in [
        OffenseReport.Resolution.FINE_PAID,
        OffenseReport.Resolution.ESCALATED,
        OffenseReport.Resolution.DISMISSED,
    ]:
        raise ValueError("Invalid resolution value.")

    if resolution == OffenseReport.Resolution.FINE_PAID:
        if offense.fine_amount is None or offense.fine_amount <= 0:
            raise ValueError("Fine amount must be set to resolve as fine paid.")

        fee_exists = FeeCollection.objects.filter(
            fee_type=FeeCollection.FeeType.OTHER,
            amount=offense.fine_amount,
            description__icontains=f"fine for offense #{offense.pk}",
        ).exists()
        if not fee_exists:
            raise ValueError("A fee collection record for the fine must be created before resolving.")

        if offense.hearings.exists() is False:
            raise ValueError("A hearing record is required before resolving an offense.")

    if resolution == OffenseReport.Resolution.ESCALATED:
        if offense.evidence.exists() is False or offense.hearings.exists() is False:
            raise ValueError("Evidence and hearing records are required for escalation to court.")

    offense.status = OffenseReport.Status.RESOLVED
    offense.resolution = resolution
    offense.save(user=resolved_by_user)

    if resolution == OffenseReport.Resolution.FINE_PAID and informant_id:
        config = SystemConfig.get()
        reward_amount = offense.fine_amount * (config.informant_reward_percent / Decimal("100"))
        InformantReward.objects.create(
            offense=offense,
            informant_id=informant_id,
            reward_amount=reward_amount,
            paid_date=date.today(),
            created_by=resolved_by_user,
            updated_by=resolved_by_user,
        )

    log_audit(
        action=AuditLog.Action.OFFENSE_RESOLVED,
        model_name="OffenseReport",
        object_id=offense.pk,
        new_value=resolution,
        reason=f"Resolved by {resolved_by_user.email}",
        user=resolved_by_user,
    )

    return offense
