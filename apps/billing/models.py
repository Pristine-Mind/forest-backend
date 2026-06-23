from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel, ReceiptSequence


class Receipt(AbstractBaseModel):
    class ReferenceType(models.TextChoices):
        SALE = "sale", _("Sale")
        FEE_COLLECTION = "fee_collection", _("Fee Collection")
        VISITOR_ENTRY = "visitor_entry", _("Visitor Entry")

    receipt_no = models.CharField(max_length=16, primary_key=True)
    reference_type = models.CharField(max_length=20, choices=ReferenceType.choices)
    reference_id = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    issued_date = models.DateField()
    issued_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_receipts",
    )
    pdf_file = models.FileField(upload_to="receipts/%Y/%m/", blank=True)

    class Meta:
        ordering = ["-issued_date", "-receipt_no"]
        verbose_name = "Receipt"
        verbose_name_plural = "Receipts"

    def __str__(self) -> str:
        return self.receipt_no

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            self.receipt_no = ReceiptSequence.next_receipt_no()
        super().save(*args, **kwargs)


class FeeCollection(AbstractBaseModel):
    class FeeType(models.TextChoices):
        MEMBERSHIP = "membership", _("Membership")
        RENEWAL = "renewal", _("Renewal")
        ROYALTY = "royalty", _("Royalty")
        OTHER = "other", _("Other")

    class PaymentStatus(models.TextChoices):
        PAID = "paid", _("Paid")
        DUE = "due", _("Due")
        PARTIAL = "partial", _("Partial")

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fee_collections",
    )
    fee_type = models.CharField(max_length=16, choices=FeeType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    payment_status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.DUE)
    receipt_no = models.OneToOneField(
        Receipt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fee_collection",
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Fee Collection"
        verbose_name_plural = "Fee Collections"

    def __str__(self) -> str:
        return f"{self.fee_type} - {self.amount} - {self.payment_status}"

    def save(self, *args, **kwargs):
        if self.amount_paid >= self.amount:
            self.payment_status = self.PaymentStatus.PAID
        elif self.amount_paid > 0:
            self.payment_status = self.PaymentStatus.PARTIAL
        else:
            self.payment_status = self.PaymentStatus.DUE
        super().save(*args, **kwargs)
