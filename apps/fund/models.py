from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel, SystemConfig


class FundAllocationRule(AbstractBaseModel):
    forest_dev_min_percent = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    poor_targeted_min_percent = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    effective_from = models.DateField()

    class Meta:
        ordering = ["-effective_from"]
        verbose_name = "Fund Allocation Rule"
        verbose_name_plural = "Fund Allocation Rules"

    def __str__(self) -> str:
        return f"Rule from {self.effective_from}"


class BudgetAllocation(AbstractBaseModel):

    class WorkStatus(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    fiscal_year = models.CharField(max_length=16)
    title = models.CharField(max_length=255)
    work_description = models.TextField(blank=True)
    allocated_amount = models.FloatField()
    approved_date = models.DateField(null=True, blank=True)
    work_status = models.CharField(
        max_length=20,
        choices=WorkStatus.choices,
        default=WorkStatus.PLANNED,
    )
    remarks = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_budget_allocations",
    )

    class Meta:
        ordering = ["-approved_date"]

    def __str__(self):
        return self.title


class BankAccount(AbstractBaseModel):
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=64)
    signatories = models.JSONField(
        default=list,
        help_text="List of CommitteeMember IDs who can sign on this account",
    )
    min_signatures_required = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"

    def __str__(self) -> str:
        return f"{self.bank_name} - {self.account_number}"

    def clean(self):
        super().clean()
        from apps.governance.models import CommitteeMember

        if not isinstance(self.signatories, list):
            raise ValidationError({"signatories": "Signatories must be a list of committee member IDs."})

        women_count = CommitteeMember.objects.filter(pk__in=self.signatories, gender__iexact="female").count()
        if women_count < 1:
            raise ValidationError({"signatories": "At least one signatory must be a woman, per the bylaws."})


class BankTransaction(AbstractBaseModel):
    class Type(models.TextChoices):
        DEPOSIT = "deposit", _("Deposit")
        WITHDRAWAL = "withdrawal", _("Withdrawal")

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="transactions")
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=16, choices=Type.choices, null=True, blank=True)
    amount = models.FloatField()
    description = models.TextField()
    requires_committee_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_bank_transactions",
    )

    class Meta:
        ordering = ["-transaction_date"]
        verbose_name = "Bank Transaction"
        verbose_name_plural = "Bank Transactions"

    def __str__(self) -> str:
        return f"{self.transaction_date} - {self.amount} - {self.description}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class CashTransaction(AbstractBaseModel):
    class Type(models.TextChoices):
        INCOME = "income", _("Income")
        EXPENSE = "expense", _("Expense")

    class PaymentType(models.TextChoices):
        CASH = "cash", _("Cash")
        CHEQUE = "cheque", _("Cheque")
        DIGITAL_WALLET = "digital_wallet", _("Digital Wallet")

    type = models.CharField(max_length=16, choices=Type.choices)
    payment_type = models.CharField(
        max_length=16,
        choices=PaymentType.choices,
        default=PaymentType.CASH,
        help_text="Payment method used for this transaction",
    )
    source_or_purpose = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    requires_committee_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_cash_transactions",
    )
    cheque_number = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Required if payment type is cheque",
    )
    cheque_bank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bank name for cheque payment",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cash Transaction"
        verbose_name_plural = "Cash Transactions"

    def __str__(self) -> str:
        return f"{self.type} - {self.source_or_purpose} - {self.amount}"

    def clean(self):
        super().clean()
        if self.payment_type == self.PaymentType.CHEQUE:
            if not self.cheque_number:
                raise ValidationError({"cheque_number": "Cheque number is required when payment type is cheque."})
            if not self.cheque_bank_name:
                raise ValidationError({"cheque_bank_name": "Bank name is required when payment type is cheque."})

    def save(self, *args, **kwargs):
        config = SystemConfig.get()
        self.requires_committee_approval = self.amount > min(
            config.cash_chair_approval_limit, config.cash_treasurer_approval_limit
        )
        super().save(*args, **kwargs)


class Audit(AbstractBaseModel):
    class Tier(models.TextChoices):
        INTERNAL = "internal", _("Internal")
        EXTERNAL = "external", _("External")

    fiscal_year = models.CharField(max_length=16)
    total_income = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    audit_tier = models.CharField(max_length=16, choices=Tier.choices, blank=True)
    auditor_name = models.CharField(max_length=255)
    findings = models.TextField(blank=True)
    irregularities_recovered = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["-fiscal_year"]
        verbose_name = "Audit"
        verbose_name_plural = "Audits"

    def __str__(self) -> str:
        return f"Audit {self.fiscal_year} - {self.audit_tier}"

    def save(self, *args, **kwargs):
        config = SystemConfig.get()
        self.audit_tier = self.Tier.EXTERNAL if self.total_income > config.audit_external_threshold else self.Tier.INTERNAL
        super().save(*args, **kwargs)


class PublicAudit(AbstractBaseModel):
    fiscal_year = models.CharField(max_length=16)
    presentation_date = models.DateField()
    assembly_approval = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fiscal_year"]
        verbose_name = "Public Audit"
        verbose_name_plural = "Public Audits"

    def __str__(self) -> str:
        return f"Public Audit {self.fiscal_year}"
