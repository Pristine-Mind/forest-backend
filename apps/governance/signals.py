from datetime import timedelta

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.core.models import SystemConfig
from apps.governance.models import CommitteeMember, HandoverRecord


@receiver(pre_save, sender=CommitteeMember)
def create_handover_record_on_removal(sender, instance, **kwargs):
    """
    Create a handover record automatically when a committee member's status
    changes away from active.
    """

    if not instance.pk:
        return

    try:
        previous = CommitteeMember.objects.get(pk=instance.pk)
    except CommitteeMember.DoesNotExist:
        return

    if previous.status == CommitteeMember.Status.ACTIVE and instance.status != CommitteeMember.Status.ACTIVE:
        config = SystemConfig.get()
        deadline = instance.term_end or (instance.updated_at.date() + timedelta(days=config.handover_deadline_days))
        HandoverRecord.objects.create(
            outgoing_committee_member=instance,
            cash_amount=0,
            deadline_date=deadline,
            status=HandoverRecord.Status.PENDING,
            created_by=instance.updated_by,
            updated_by=instance.updated_by,
        )


def check_committee_composition_quota():
    """
    Check active committee composition against configured gender/caste quotas.
    Returns a dict of flags (not a blocker).
    """

    config = SystemConfig.get()
    active_members = CommitteeMember.objects.filter(status=CommitteeMember.Status.ACTIVE)
    total = active_members.count()
    female_count = active_members.filter(gender__iexact="female").count()

    # Treat "dalit" or any non-blank caste_ethnicity as a minority/diversity member for flagging.
    # Adjust the filter as needed for the CFUG's specific quota categories.
    minority_count = active_members.exclude(caste_ethnicity__iexact="").count()

    return {
        "total_active": total,
        "female_count": female_count,
        "min_female_required": config.min_female_committee_members,
        "female_quota_met": female_count >= config.min_female_committee_members,
        "minority_count": minority_count,
        "min_minority_required": config.min_dalit_or_minority_committee_members,
        "minority_quota_met": minority_count >= config.min_dalit_or_minority_committee_members,
    }
