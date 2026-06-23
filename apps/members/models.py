from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel, SystemConfig


class Household(AbstractBaseModel):
    class WealthClass(models.TextChoices):
        RICH = "rich", _("Rich")
        MEDIUM = "medium", _("Medium")
        POOR = "poor", _("Poor")

    class EducationLevel(models.TextChoices):
        ILLITERATE = "illiterate", _("Illiterate")
        BASIC = "basic", _("Basic")
        SECONDARY_PLUS = "secondary_plus", _("Secondary+")

    class EntryFeeType(models.TextChoices):
        NEW_HOUSEHOLD = "new_household", _("New household")
        SPLIT_HOUSEHOLD = "split_household", _("Split household")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")

    household_head_name = models.CharField(max_length=255)
    tole = models.CharField(max_length=255, blank=True)
    wealth_class = models.CharField(max_length=16, choices=WealthClass.choices)

    population_male = models.PositiveIntegerField(default=0)
    population_female = models.PositiveIntegerField(default=0)

    livestock_cattle = models.PositiveIntegerField(default=0)
    livestock_buffalo = models.PositiveIntegerField(default=0)
    livestock_goat = models.PositiveIntegerField(default=0)

    education_level = models.CharField(max_length=16, choices=EducationLevel.choices, blank=True)
    occupation = models.CharField(max_length=255, blank=True)
    caste_ethnicity = models.CharField(max_length=255, blank=True)

    registration_date = models.DateField()
    entry_fee_type = models.CharField(max_length=16, choices=EntryFeeType.choices, default=EntryFeeType.NEW_HOUSEHOLD)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["household_head_name"]
        verbose_name = "Household"
        verbose_name_plural = "Households"

    def __str__(self) -> str:
        return f"{self.household_head_name} ({self.tole or 'no tole'})"

    @property
    def entry_fee_due(self) -> Decimal:
        config = SystemConfig.get()
        if self.entry_fee_type == self.EntryFeeType.SPLIT_HOUSEHOLD:
            return config.split_household_entry_fee
        return config.new_household_entry_fee


class Member(AbstractBaseModel):
    class MembershipType(models.TextChoices):
        GENERAL = "general", _("General")
        LIFETIME = "lifetime", _("Lifetime")
        INSTITUTIONAL = "institutional", _("Institutional")
        SPECIAL = "special", _("Special")
        OTHER = "other", _("Other")

    class MembershipStatus(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        CANCELLED = "cancelled", _("Cancelled")

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="members")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="member_profile",
    )
    full_name = models.CharField(max_length=255)
    citizenship_no = models.CharField(max_length=64, unique=True, db_index=True)
    membership_type = models.CharField(max_length=16, choices=MembershipType.choices, default=MembershipType.GENERAL)
    membership_status = models.CharField(
        max_length=16,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )
    date_joined = models.DateField()

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Member"
        verbose_name_plural = "Members"

    def __str__(self) -> str:
        return self.full_name

    def last_renewal(self) -> MembershipRenewal | None:
        return self.renewals.order_by("-fiscal_year").first()

    def fee_tier_for_year(self, fiscal_year: str) -> MembershipRenewal.FeeTier:
        """
        Compute fee tier based on elapsed unrenewed years.
        This is a simplified calculation: uses the configured cancellation years
        and the gap between the latest renewal fiscal year and the requested one.
        """
        config = SystemConfig.get()
        last = self.last_renewal()
        if last is None:
            years = 0
        else:
            try:
                last_year = int(last.fiscal_year.split("/")[0])
                current_year = int(fiscal_year.split("/")[0])
                years = max(0, current_year - last_year)
            except (ValueError, IndexError):
                years = 1

        if years <= 1:
            return MembershipRenewal.FeeTier.ON_TIME
        if years <= 3:
            return MembershipRenewal.FeeTier.OVERDUE_3YR
        if years <= 5:
            return MembershipRenewal.FeeTier.OVERDUE_5YR
        return MembershipRenewal.FeeTier.OVERDUE_5YR_PLUS

    def renewal_fee_for_tier(self, tier: MembershipRenewal.FeeTier) -> Decimal:
        config = SystemConfig.get()
        mapping = {
            MembershipRenewal.FeeTier.ON_TIME: config.renewal_fee_on_time,
            MembershipRenewal.FeeTier.OVERDUE_3YR: config.renewal_fee_overdue_3yr,
            MembershipRenewal.FeeTier.OVERDUE_5YR: config.renewal_fee_overdue_5yr,
            MembershipRenewal.FeeTier.OVERDUE_5YR_PLUS: config.renewal_fee_overdue_5yr_plus,
        }
        return mapping[tier]


class MembershipRenewal(AbstractBaseModel):
    class FeeTier(models.TextChoices):
        ON_TIME = "on_time", _("On time")
        OVERDUE_3YR = "overdue_3yr", _("Overdue up to 3 years")
        OVERDUE_5YR = "overdue_5yr", _("Overdue up to 5 years")
        OVERDUE_5YR_PLUS = "overdue_5yr_plus", _("Overdue more than 5 years")

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="renewals")
    fiscal_year = models.CharField(max_length=16)
    fee_tier = models.CharField(max_length=16, choices=FeeTier.choices)
    fee_charged = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    paid_date = models.DateField()

    class Meta:
        ordering = ["-fiscal_year"]
        verbose_name = "Membership Renewal"
        verbose_name_plural = "Membership Renewals"
        constraints = [models.UniqueConstraint(fields=["member", "fiscal_year"], name="unique_member_fiscal_year")]

    def __str__(self) -> str:
        return f"{self.member.full_name} - {self.fiscal_year}"
