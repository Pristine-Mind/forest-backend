from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel


class HarvestRequest(AbstractBaseModel):
    class SourceType(models.TextChoices):
        MEMBER_REQUESTED = "member_requested", _("Member Requested")
        FOREST_INITIATED = "forest_initiated", _("Forest Initiated")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="harvest_requests",
    )
    operation_name = models.CharField(max_length=255, blank=True)
    species = models.ForeignKey("forest.Species", on_delete=models.CASCADE, related_name="harvest_requests")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    requested_date = models.DateField()
    approved_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_harvests",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_date"]
        verbose_name = "Harvest Request"
        verbose_name_plural = "Harvest Requests"

    def __str__(self) -> str:
        return f"{self.source_type} - {self.species} - {self.quantity}"

    def clean(self):
        super().clean()
        if self.source_type == self.SourceType.MEMBER_REQUESTED:
            if not self.member:
                raise ValidationError({"member": "Member is required for member-requested harvests."})
            if self.member.household.membership_status != self.member.household.MembershipStatus.ACTIVE:
                raise ValidationError({"member": "Only active members may submit a harvest request."})
            if self.operation_name:
                raise ValidationError({"operation_name": "Operation name must be blank for member-requested harvests."})
        else:
            if self.member:
                raise ValidationError({"member": "Member must be blank for forest-initiated harvests."})
            if not self.operation_name:
                raise ValidationError({"operation_name": "Operation name is required for forest-initiated harvests."})

        if self.status == self.Status.REJECTED and not self.notes:
            raise ValidationError({"notes": "Notes are required when rejecting a request."})
