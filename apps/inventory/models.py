from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel


class StockLedger(AbstractBaseModel):
    species = models.ForeignKey("forest.Species", on_delete=models.CASCADE, related_name="stock_ledgers")
    grade = models.CharField(max_length=16)

    class Meta:
        ordering = ["species__species_name", "grade"]
        verbose_name = "Stock Ledger"
        verbose_name_plural = "Stock Ledgers"
        constraints = [models.UniqueConstraint(fields=["species", "grade"], name="unique_species_grade_stock")]

    def __str__(self) -> str:
        return f"{self.species.species_name} - Grade {self.grade}"

    @property
    def quantity_available(self) -> Decimal:
        total = self.transactions.aggregate(
            total=models.Sum(
                models.Case(
                    models.When(transaction_type=StockTransaction.Type.IN, then=models.F("quantity")),
                    models.When(transaction_type=StockTransaction.Type.OUT, then=-models.F("quantity")),
                    default=models.Value(0),
                    output_field=models.DecimalField(),
                )
            )
        )["total"]
        return total or Decimal("0.00")


class StockTransaction(AbstractBaseModel):
    class Type(models.TextChoices):
        IN = "in", _("In")
        OUT = "out", _("Out")

    class ReferenceType(models.TextChoices):
        HARVEST = "harvest", _("Harvest")
        SALE = "sale", _("Sale")
        ADJUSTMENT = "adjustment", _("Adjustment")

    stock = models.ForeignKey(StockLedger, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=8, choices=Type.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    reference_type = models.CharField(max_length=16, choices=ReferenceType.choices)
    reference_id = models.PositiveIntegerField()
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Stock Transaction"
        verbose_name_plural = "Stock Transactions"

    def __str__(self) -> str:
        return f"{self.transaction_type} {self.quantity} for {self.stock}"


class PriceRate(AbstractBaseModel):
    class BuyerType(models.TextChoices):
        MEMBER = "member", _("Member")
        OUTSIDER = "outsider", _("Outsider")

    species = models.ForeignKey("forest.Species", on_delete=models.CASCADE, related_name="price_rates")
    grade = models.CharField(max_length=16)
    buyer_type = models.CharField(max_length=16, choices=BuyerType.choices)
    rate_per_unit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    effective_from = models.DateField()

    class Meta:
        ordering = ["-effective_from"]
        verbose_name = "Price Rate"
        verbose_name_plural = "Price Rates"
        constraints = [
            models.UniqueConstraint(
                fields=["species", "grade", "buyer_type", "effective_from"],
                name="unique_price_rate",
            )
        ]

    def __str__(self) -> str:
        return f"{self.species} - {self.grade} - {self.buyer_type} @ {self.rate_per_unit}"


class Sale(AbstractBaseModel):
    class BuyerType(models.TextChoices):
        MEMBER = "member", _("Member")
        OUTSIDER = "outsider", _("Outsider")

    class PaymentStatus(models.TextChoices):
        PAID = "paid", _("Paid")
        DUE = "due", _("Due")
        PARTIAL = "partial", _("Partial")

    buyer_name = models.CharField(max_length=255)
    buyer_type = models.CharField(max_length=16, choices=BuyerType.choices)
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )
    species = models.ForeignKey("forest.Species", on_delete=models.CASCADE, related_name="sales")
    grade = models.CharField(max_length=16)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    rate_applied = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Auto-filled from price rate; editable by committee with audit note",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    payment_status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.DUE)
    receipt_no = models.OneToOneField(
        "billing.Receipt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sale",
    )
    audit_note = models.TextField(
        blank=True,
        help_text="Reason if rate_applied was manually edited by the committee",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

    def __str__(self) -> str:
        return f"Sale to {self.buyer_name} - {self.quantity} {self.species}"

    def clean(self):
        super().clean()
        if self.buyer_type == self.BuyerType.MEMBER and not self.member:
            raise ValidationError({"member": "Member is required when buyer type is member."})
        if self.buyer_type == self.BuyerType.OUTSIDER and self.member:
            raise ValidationError({"member": "Member must be blank when buyer type is outsider."})

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.rate_applied
        super().save(*args, **kwargs)
