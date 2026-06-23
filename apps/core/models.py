from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.managers import UserManager


class AbstractBaseModel(models.Model):
    """Base model for all project models."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        editable=False,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Avoid importing User in a way that creates circular imports
        from django.contrib.auth import get_user_model

        user = kwargs.pop("user", None)
        if user is None:
            user = getattr(self, "_current_user", None)
        if user is not None:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model supporting the CFUG RBAC roles."""

    class Role(models.TextChoices):
        COMMITTEE_OFFICER = "committee_officer", _("Committee Officer")
        MEMBER = "member", _("Member")
        SUB_COMMITTEE_MEMBER = "sub_committee_member", _("Sub-committee Member")
        DFO_VIEWER = "dfo_viewer", _("DFO Viewer")
        ADMIN = "admin", _("System Administrator")

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    role = models.CharField(
        max_length=24,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
    )

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. " "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        return self.email

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def is_committee_officer(self) -> bool:
        return self.role == self.Role.COMMITTEE_OFFICER or self.is_superuser

    def is_dfo_viewer(self) -> bool:
        return self.role == self.Role.DFO_VIEWER or self.is_superuser

    def is_member_user(self) -> bool:
        return self.role == self.Role.MEMBER

    def is_sub_committee_user(self) -> bool:
        return self.role == self.Role.SUB_COMMITTEE_MEMBER


class SystemConfig(AbstractBaseModel):
    """Singleton holding all CFUG-bylaws configurable values."""

    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configuration"

    # Membership fees
    new_household_entry_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("100.00"))
    split_household_entry_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("50.00"))
    renewal_fee_on_time = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("50.00"))
    renewal_fee_overdue_3yr = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("100.00"))
    renewal_fee_overdue_5yr = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("200.00"))
    renewal_fee_overdue_5yr_plus = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("300.00"))
    membership_cancellation_years = models.PositiveSmallIntegerField(default=5)
    current_fiscal_year = models.CharField(max_length=16, default="2082/83")

    # Fund allocation
    forest_dev_min_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("50.00"))
    poor_targeted_min_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("25.00"))

    # Cash approval limits
    cash_chair_approval_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("5000.00"))
    cash_treasurer_approval_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("10000.00"))

    # Audit
    audit_external_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("50000.00"))

    # Offense
    informant_reward_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("10.00"))

    # Governance
    no_confidence_signature_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("25.00"))
    handover_deadline_days = models.PositiveSmallIntegerField(default=7)

    # Committee composition quotas (used for flagging, not blocking)
    min_female_committee_members = models.PositiveSmallIntegerField(default=2)
    min_dalit_or_minority_committee_members = models.PositiveSmallIntegerField(default=1)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        self.invalidate_cache()

    def delete(self, *args, **kwargs):
        raise NotImplementedError("SystemConfig is a singleton and cannot be deleted.")

    @classmethod
    def get(cls) -> "SystemConfig":
        cache_key = "system_config_singleton"
        from django.core.cache import cache

        try:
            config = cache.get(cache_key)
        except Exception:
            config = None

        if config is None:
            config, _ = cls.objects.get_or_create(pk=1)
            try:
                cache.set(cache_key, config, timeout=3600)
            except Exception:
                pass
        return config

    def invalidate_cache(self):
        from django.core.cache import cache

        try:
            cache.delete("system_config_singleton")
        except Exception:
            pass


class AuditLog(AbstractBaseModel):
    """Audit trail for sensitive changes."""

    class Action(models.TextChoices):
        TREE_COUNT_ADJUSTMENT = "tree_count_adjustment", _("Tree count adjustment")
        WEALTH_CLASS_CHANGE = "wealth_class_change", _("Wealth classification change")
        FUND_RULE_CHANGE = "fund_rule_change", _("Fund allocation rule change")
        HARVEST_APPROVAL = "harvest_approval", _("Harvest approval")
        HARVEST_REJECTION = "harvest_rejection", _("Harvest rejection")
        SALE_RECORDED = "sale_recorded", _("Sale recorded")
        OFFENSE_RESOLVED = "offense_resolved", _("Offense resolved")
        MEMBERSHIP_CANCELLATION = "membership_cancellation", _("Membership cancellation")
        MANUAL_OVERRIDE = "manual_override", _("Manual override")

    action = models.CharField(max_length=32, choices=Action.choices)
    model_name = models.CharField(max_length=64)
    object_id = models.CharField(max_length=64, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self) -> str:
        return f"{self.action} on {self.model_name}"


class ReceiptSequence(models.Model):
    """Protected counter for globally unique receipt numbers."""

    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Receipt Sequence"
        verbose_name_plural = "Receipt Sequence"

    @classmethod
    def next_receipt_no(cls) -> str:
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(pk=1)
            seq.last_number += 1
            seq.save(update_fields=["last_number"])
            return f"RCP-{seq.last_number:06d}"
