from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel


class VisitorFeeRate(AbstractBaseModel):
    class VisitPurpose(models.TextChoices):
        GENERAL_VISIT = "general_visit", _("General Visit")
        STUDY_RESEARCH = "study_research", _("Study / Research")

    visit_purpose = models.CharField(max_length=20, choices=VisitPurpose.choices, unique=True)
    fee_per_visitor_per_day = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    class Meta:
        verbose_name = "Visitor Fee Rate"
        verbose_name_plural = "Visitor Fee Rates"

    def __str__(self) -> str:
        return f"{self.visit_purpose} - {self.fee_per_visitor_per_day}"


class VisitorEntry(AbstractBaseModel):
    class VisitPurpose(models.TextChoices):
        GENERAL_VISIT = "general_visit", _("General Visit")
        STUDY_RESEARCH = "study_research", _("Study / Research")

    entry_date = models.DateField()
    visit_purpose = models.CharField(max_length=20, choices=VisitPurpose.choices)
    visitor_count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    fee_waived = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    receipt_no = models.OneToOneField(
        "billing.Receipt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visitor_entry",
    )

    class Meta:
        ordering = ["-entry_date"]
        verbose_name = "Visitor Entry"
        verbose_name_plural = "Visitor Entries"

    def __str__(self) -> str:
        return f"{self.visitor_count} visitors on {self.entry_date}"

    def save(self, *args, **kwargs):
        if self.fee_waived:
            self.total_amount = Decimal("0.00")
        else:
            rate = VisitorFeeRate.objects.filter(visit_purpose=self.visit_purpose).first()
            fee = rate.fee_per_visitor_per_day if rate else Decimal("0.00")
            self.total_amount = Decimal(self.visitor_count) * Decimal(self.days) * fee
        super().save(*args, **kwargs)


class OfficialGuestLog(AbstractBaseModel):
    visitor_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255, blank=True)
    visit_start_date = models.DateField()
    visit_end_date = models.DateField()
    comments_or_guidance = models.TextField(blank=True)

    class Meta:
        ordering = ["-visit_start_date"]
        verbose_name = "Official Guest Log"
        verbose_name_plural = "Official Guest Logs"

    def __str__(self) -> str:
        return f"{self.visitor_name} - {self.visit_start_date} to {self.visit_end_date}"
