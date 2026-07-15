from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel


class CommitteeMember(AbstractBaseModel):
    class Position(models.TextChoices):
        CHAIR = "chair", _("Chair")
        VICE_CHAIR = "vice_chair", _("Vice Chair")
        SECRETARY = "secretary", _("Secretary")
        JOINT_SECRETARY = "joint_secretary", _("Joint Secretary")
        TREASURER = "treasurer", _("Treasurer")
        MEMBER = "member", _("Member")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        VACANT = "vacant", _("Vacant")
        REMOVED = "removed", _("Removed")

    member = models.ForeignKey("members.Household", on_delete=models.CASCADE, related_name="committee_roles")
    position = models.CharField(max_length=20, choices=Position.choices)
    gender = models.CharField(max_length=16)
    caste_ethnicity = models.CharField(max_length=255, blank=True)
    term_start = models.DateField()
    term_end = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    subcommittees = models.ManyToManyField("SubCommittee", blank=True, related_name="committee_members")
    photo = models.ImageField(upload_to="committee_members/", blank=True, null=True)

    class Meta:
        ordering = ["-term_start", "position"]
        verbose_name = "Committee Member"
        verbose_name_plural = "Committee Members"

    def __str__(self) -> str:
        return f"{self.member.household_head_name} - {self.position}"


class Election(AbstractBaseModel):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    election_committee_members = models.TextField(help_text="Names / designations of the election committee members")
    election_date = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)

    class Meta:
        ordering = ["-election_date"]
        verbose_name = "Election"
        verbose_name_plural = "Elections"

    def __str__(self) -> str:
        return f"Election on {self.election_date}"


class Candidate(AbstractBaseModel):
    class Result(models.TextChoices):
        ELECTED = "elected", _("Elected")
        NOT_ELECTED = "not_elected", _("Not Elected")

    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="candidates")
    member = models.ForeignKey("members.Household", on_delete=models.CASCADE, related_name="candidacies")
    position_applied = models.CharField(max_length=64)
    votes_received = models.PositiveIntegerField(default=0)
    result = models.CharField(max_length=16, choices=Result.choices, default=Result.NOT_ELECTED)

    class Meta:
        ordering = ["-votes_received"]
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"

    def __str__(self) -> str:
        return f"{self.member.household_head_name} for {self.position_applied}"


class SubCommittee(AbstractBaseModel):
    class Name(models.TextChoices):
        ACCOUNT_FUND = "account_fund", _("Account / Fund")
        DISPUTE_RESOLUTION = "dispute_resolution", _("Dispute Resolution")
        INFRASTRUCTURE = "infrastructure", _("Infrastructure")
        MONITORING = "monitoring", _("Monitoring")
        LIVELIHOOD = "livelihood", _("Livelihood")
        ANTI_POACHING = "anti_poaching", _("Anti Poaching")
        FIRE_CONTROL = "fire_control", _("Fire Control")
        YOUTH_SPORTS = "youth_sports", _("Youth / Sports")
        WOMEN = "women", _("Women")
        OTHER = "other", _("Other")

    name = models.CharField(max_length=32, choices=Name.choices, unique=True)
    tor_description = models.TextField()

    class Meta:
        verbose_name = "Sub-committee"
        verbose_name_plural = "Sub-committees"

    def __str__(self) -> str:
        return self.get_name_display()


class OathRecord(AbstractBaseModel):
    committee_member = models.ForeignKey(CommitteeMember, on_delete=models.CASCADE, related_name="oaths")
    oath_date = models.DateField()

    class Meta:
        ordering = ["-oath_date"]
        verbose_name = "Oath Record"
        verbose_name_plural = "Oath Records"

    def __str__(self) -> str:
        return f"Oath of {self.committee_member} on {self.oath_date}"


class NoConfidenceMotion(AbstractBaseModel):
    class TargetType(models.TextChoices):
        FULL_COMMITTEE = "full_committee", _("Full Committee")
        SINGLE_OFFICER = "single_officer", _("Single Officer")

    class Decision(models.TextChoices):
        PENDING = "pending", _("Pending")
        PASSED = "passed", _("Passed")
        FAILED = "failed", _("Failed")

    target_type = models.CharField(max_length=16, choices=TargetType.choices)
    target_committee_member = models.ForeignKey(
        CommitteeMember,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="no_confidence_motions",
    )
    signatures_count = models.PositiveIntegerField(default=0)
    filed_date = models.DateField()
    assembly_decision = models.CharField(max_length=16, choices=Decision.choices, default=Decision.PENDING)

    class Meta:
        ordering = ["-filed_date"]
        verbose_name = "No-confidence Motion"
        verbose_name_plural = "No-confidence Motions"

    def __str__(self) -> str:
        return f"Motion against {self.target_type} on {self.filed_date}"

    def clean(self):
        super().clean()
        if self.target_type == self.TargetType.SINGLE_OFFICER and not self.target_committee_member:
            raise ValidationError({"target_committee_member": "Required when target is a single officer."})
        if self.target_type == self.TargetType.FULL_COMMITTEE and self.target_committee_member:
            raise ValidationError({"target_committee_member": "Must be blank when target is the full committee."})


class HandoverRecord(AbstractBaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        COMPLETED = "completed", _("Completed")
        ESCALATED = "escalated", _("Escalated")

    outgoing_committee_member = models.ForeignKey(
        CommitteeMember,
        on_delete=models.CASCADE,
        related_name="handovers_outgoing",
    )
    incoming_committee_member = models.ForeignKey(
        CommitteeMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handovers_incoming",
    )
    cash_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    assets_summary = models.TextField(blank=True)
    deadline_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-deadline_date"]
        verbose_name = "Handover Record"
        verbose_name_plural = "Handover Records"

    def __str__(self) -> str:
        return f"Handover from {self.outgoing_committee_member}"
