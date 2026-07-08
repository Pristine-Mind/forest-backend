from celery import shared_task

from apps.core.models import SystemConfig
from apps.members.models import Household, Member, MembershipRenewal


@shared_task
def check_membership_cancellation():
    """
    Nightly task that cancels memberships that have exceeded the configured
    consecutive unrenewed year threshold.
    """

    config = SystemConfig.get()
    cancelled = 0

    for member in Member.objects.filter(household__membership_status=Household.MembershipStatus.ACTIVE):
        last = member.last_renewal()
        if last is None:
            continue

        try:
            last_year = int(last.fiscal_year.split("/")[0])
            current_year = int(config.current_fiscal_year.split("/")[0])
            years = max(0, current_year - last_year)
        except (ValueError, AttributeError, IndexError):
            continue

        if years > config.membership_cancellation_years:
            member.household.membership_status = Household.MembershipStatus.CANCELLED
            member.household.save()
            cancelled += 1

    return f"Cancelled {cancelled} memberships."
