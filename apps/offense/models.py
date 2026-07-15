from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel


class OffenseReport(AbstractBaseModel):
    class Status(models.TextChoices):
        REPORTED = "reported", _("Reported")
        INVESTIGATING = "investigating", _("Investigating")
        RESOLVED = "resolved", _("Resolved")
        ESCALATED_TO_COURT = "escalated_to_court", _("Escalated to Court")

    class Resolution(models.TextChoices):
        FINE_PAID = "fine_paid", _("Fine Paid")
        ESCALATED = "escalated", _("Escalated")
        DISMISSED = "dismissed", _("Dismissed")

    reported_by = models.ForeignKey(
        "members.Household",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_offenses",
    )
    accused_name = models.CharField(max_length=255)
    offense_type = models.CharField(max_length=255)
    description = models.TextField()
    report_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REPORTED)
    damage_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    fine_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    resolution = models.CharField(max_length=16, choices=Resolution.choices, null=True, blank=True)
    informant = models.ForeignKey(
        "members.Household",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="informant_rewards",
    )

    class Meta:
        ordering = ["-report_date"]
        verbose_name = "Offense Report"
        verbose_name_plural = "Offense Reports"

    def __str__(self) -> str:
        return f"{self.offense_type} - {self.accused_name} ({self.status})"


class EvidenceItem(AbstractBaseModel):
    class ItemType(models.TextChoices):
        TOOL = "tool", _("Tool")
        WEAPON = "weapon", _("Weapon")
        VEHICLE = "vehicle", _("Vehicle")
        FOREST_PRODUCT = "forest_product", _("Forest Product")

    offense = models.ForeignKey(OffenseReport, on_delete=models.CASCADE, related_name="evidence")
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    description = models.TextField()
    confiscated_date = models.DateField()

    class Meta:
        ordering = ["-confiscated_date"]
        verbose_name = "Evidence Item"
        verbose_name_plural = "Evidence Items"

    def __str__(self) -> str:
        return f"{self.item_type} for offense #{self.offense_id}"


class HearingRecord(AbstractBaseModel):
    class Outcome(models.TextChoices):
        ADMITTED = "admitted", _("Admitted")
        DENIED = "denied", _("Denied")

    offense = models.ForeignKey(OffenseReport, on_delete=models.CASCADE, related_name="hearings")
    accused_statement = models.TextField(blank=True)
    hearing_date = models.DateField()
    outcome = models.CharField(max_length=16, choices=Outcome.choices)

    class Meta:
        ordering = ["-hearing_date"]
        verbose_name = "Hearing Record"
        verbose_name_plural = "Hearing Records"

    def __str__(self) -> str:
        return f"Hearing for offense #{self.offense_id} on {self.hearing_date}"


class InformantReward(AbstractBaseModel):
    offense = models.OneToOneField(OffenseReport, on_delete=models.CASCADE, related_name="reward")
    informant = models.ForeignKey(
        "members.Household",
        on_delete=models.CASCADE,
        related_name="rewards_received",
    )
    reward_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    paid_date = models.DateField()

    class Meta:
        verbose_name = "Informant Reward"
        verbose_name_plural = "Informant Rewards"

    def __str__(self) -> str:
        return f"Reward to {self.informant.full_name} - {self.reward_amount}"


class PatrolLog(AbstractBaseModel):
    watcher = models.ForeignKey(
        "members.Household",
        on_delete=models.CASCADE,
        related_name="patrol_logs",
    )
    patrol_date = models.DateField()
    notes = models.TextField(blank=True)
    offense = models.ForeignKey(
        OffenseReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patrol_logs",
    )

    class Meta:
        ordering = ["-patrol_date"]
        verbose_name = "Patrol Log"
        verbose_name_plural = "Patrol Logs"

    def __str__(self) -> str:
        return f"Patrol by {self.watcher.full_name} on {self.patrol_date}"
