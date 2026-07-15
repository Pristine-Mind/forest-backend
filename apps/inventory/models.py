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

    buyer_name = models.CharField(max_length=255, null=True, blank=True)
    buyer_type = models.CharField(max_length=16, choices=BuyerType.choices)
    member = models.ForeignKey(
        "members.Household",
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
        null=True,
        blank=True,
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
        if self.buyer_name is None or self.member is None:
            raise ValidationError("Either buyer_name or member must be provided.")
        super().save(*args, **kwargs)


class TimberLogEntry(models.Model):
    class GRADE_CHOICES(models.TextChoices):
        A = "A", _("A")
        B = "B", _("B")
        C = "C", _("C")

    species = models.ForeignKey(
        "forest.Species",
        on_delete=models.CASCADE,
        related_name="timber_log_entries",
    )
    tree_no = models.CharField(
        max_length=20,
        verbose_name="Tree No.",
        help_text="रुख नं.",
    )
    tree_golia_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Tree's Log No.",
        help_text="रुखको गोलिया नं.",
    )
    golia_no = models.CharField(
        max_length=20,
        verbose_name="Log (Golia) No.",
        help_text="गोलिया नं.",
    )
    girth_inch = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Girth (inch)",
        help_text="गोलाई (घेरा), इन्चमा",
    )
    length_feet = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Length (ft)",
        help_text="लम्बाई, फिटमा",
    )
    volume_cubic_feet = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Volume (cu.ft)",
        help_text="आयतन (घन फिट)",
    )
    total_pieces = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Pieces",
        help_text="ढेड्रो टुक्रा जम्मा",
    )
    timber1_pieces = models.PositiveIntegerField(
        default=0,
        verbose_name="Timber No.1 - Pieces",
        help_text="टिम्बर नं. १ - व्यास नं. १ को टुक्रा",
    )
    timber1_diameter_1_inch = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Timber No.1 - Diameter 1 (inch)",
    )
    timber1_diameter_2_inch = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Timber No.1 - Diameter 2 (inch)",
    )
    timber2_pieces = models.PositiveIntegerField(
        default=0,
        verbose_name="Timber No.2 - Pieces",
        help_text="टिम्बर नं. २ - व्यास नं. १ को टुक्रा",
    )
    timber2_diameter_1_inch = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Timber No.2 - Diameter 1 (inch)",
    )
    timber2_diameter_2_inch = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Timber No.2 - Diameter 2 (inch)",
    )
    avg_diameter_length_1_feet = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Avg. Diameter Length 1 (ft)",
        help_text="औसत व्यासको लम्बाई (फि.)",
    )
    avg_diameter_length_2_feet = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Avg. Diameter Length 2 (ft)",
        help_text="औसत व्यासको लम्बाई (फि.)",
    )
    sawn_volume_cft = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Sawn Volume (Cft)",
        help_text="चिरिएको काठको आयतन (Volume, Cft)",
    )
    wastage_percent = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Wastage (%)",
        help_text="ढेड्रोको प्रतिशत (waste percentage)",
    )
    net_volume_cft = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Net Volume (Cft)",
        help_text="नेट आयतन (क्यु.फि.)",
    )
    grade = models.CharField(
        max_length=5,
        choices=GRADE_CHOICES.choices,
        verbose_name="Log Grade",
        help_text="गोलियाको ग्रेड (A / B / C)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Timber Log Entry"
        verbose_name_plural = "Timber Log Entries"
        indexes = [
            models.Index(fields=["golia_no"]),
        ]

    def __str__(self):
        return f"#{self.serial_no} - Tree {self.tree_no} / Log {self.golia_no} ({self.grade})"
