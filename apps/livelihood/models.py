from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel


class RevolvingFundLoan(AbstractBaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        REPAID = "repaid", _("Repaid")
        DEFAULTED = "defaulted", _("Defaulted")

    household = models.ForeignKey("members.Household", on_delete=models.CASCADE, related_name="revolving_loans")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    issue_date = models.DateField()
    repaid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-issue_date"]
        verbose_name = "Revolving Fund Loan"
        verbose_name_plural = "Revolving Fund Loans"

    def __str__(self) -> str:
        return f"Loan to {self.household.household_head_name} - {self.amount}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.household.wealth_class != self.household.WealthClass.POOR:
            raise ValidationError({"household": "Revolving fund loans are only available to poor households."})


class LivelihoodProgramRecord(AbstractBaseModel):
    class ProgramType(models.TextChoices):
        SKILL_TRAINING = "skill_training", _("Skill Training")
        LIVESTOCK = "livestock", _("Livestock")
        AGRICULTURE = "agriculture", _("Agriculture")
        OTHER = "other", _("Other")

    household = models.ForeignKey("members.Household", on_delete=models.CASCADE, related_name="livelihood_programs")
    program_type = models.CharField(max_length=20, choices=ProgramType.choices)
    amount_or_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    program_date = models.DateField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-program_date"]
        verbose_name = "Livelihood Program Record"
        verbose_name_plural = "Livelihood Program Records"

    def __str__(self) -> str:
        return f"{self.program_type} for {self.household.household_head_name}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.household.wealth_class != self.household.WealthClass.POOR:
            raise ValidationError({"household": "Livelihood programs are only available to poor households."})


class PovertyGroupAgreement(AbstractBaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        ENDED = "ended", _("Ended")
        TERMINATED_EARLY = "terminated_early", _("Terminated Early")

    subgroup_name = models.CharField(max_length=255)
    member_households = models.JSONField(default=list, help_text="List of Household IDs in this poverty group")
    forest_land_area = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    term_start = models.DateField()
    term_end = models.DateField()
    revenue_share_percent = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-term_start"]
        verbose_name = "Poverty Group Agreement"
        verbose_name_plural = "Poverty Group Agreements"

    def __str__(self) -> str:
        return self.subgroup_name

    def clean(self):
        super().clean()
        if not isinstance(self.member_households, list):
            raise ValidationError({"member_households": "Must be a list of household IDs."})
