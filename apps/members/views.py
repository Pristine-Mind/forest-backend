from django.db.models import Count, Q, Sum
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.core.models import SystemConfig, User
from apps.core.permissions import (
    IsCommitteeOfficer,
    IsDFOViewer,
    IsMember,
    IsSubCommitteeMember,
)
from apps.members.models import Household, Member, MembershipRenewal
from apps.members.serializers import (
    HouseholdSerializer,
    MemberDetailStatsSerializer,
    MemberListSerializer,
    MemberSerializer,
    MembershipRenewalSerializer,
    MemberStatsAggregateSerializer,
    UserMemberStatsSerializer,
)


def _member_filter_for_user(user):
    """Return a Q object limiting members/households to the user's linked profile."""

    if user.is_member_user() or user.is_sub_committee_user():
        member = getattr(user, "member_profile", None)
        if member is None:
            return Q(pk=None)  # no access
        return Q(pk=member.household_id)
    return Q()


class HouseholdViewSet(viewsets.ModelViewSet):
    queryset = Household.objects.all()
    serializer_class = HouseholdSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer]
    filterset_fields = ["wealth_class", "tole", "status"]
    search_fields = ["household_head_name", "tole"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_officer() or user.is_dfo_viewer():
            return self.queryset
        return self.queryset.filter(_member_filter_for_user(user))

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.select_related("household", "user")
    serializer_class = MemberSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer]
    filterset_fields = ["membership_type", "membership_status", "household", "household__wealth_class"]
    search_fields = ["full_name", "citizenship_no"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_officer() or user.is_dfo_viewer():
            return self.queryset
        if user.is_member_user() or user.is_sub_committee_user():
            return self.queryset.filter(user=user)
        return self.queryset.none()

    def get_serializer_class(self):
        if self.action == "list":
            return MemberListSerializer
        return super().get_serializer_class()


class MembershipRenewalViewSet(viewsets.ModelViewSet):
    queryset = MembershipRenewal.objects.select_related("member")
    serializer_class = MembershipRenewalSerializer
    permission_classes = [IsCommitteeOfficer]
    filterset_fields = ["fiscal_year", "fee_tier"]
    search_fields = ["member__full_name", "member__citizenship_no"]

    def perform_create(self, serializer):
        # This view is restricted to committee officers; renewal logic is handled
        # in the billing service for normal workflows, but direct creation is allowed
        # for administrative corrections.
        serializer.save(user=self.request.user)


class MemberDetailStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides detailed statistics for individual members including all system associations."""

    queryset = Member.objects.select_related("household", "user")
    serializer_class = MemberDetailStatsSerializer
    permission_classes = [IsCommitteeOfficer | IsDFOViewer]
    filterset_fields = ["membership_type", "membership_status", "household__wealth_class"]
    search_fields = ["full_name", "citizenship_no"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_officer() or user.is_dfo_viewer():
            return self.queryset
        return self.queryset.none()


class MemberStatsViewSet(viewsets.ViewSet):
    """Provides aggregate statistics across members with filtering options."""

    permission_classes = [IsCommitteeOfficer | IsDFOViewer]

    @action(detail=False, methods=["get"])
    def aggregate(self, request):
        """Get aggregate statistics across all or filtered members."""
        # Get base queryset
        members = Member.objects.select_related("household")

        # Apply filters
        status_filter = request.query_params.get("status", None)
        wealth_filter = request.query_params.get("wealth_class", None)
        membership_type_filter = request.query_params.get("membership_type", None)

        if status_filter:
            members = members.filter(membership_status=status_filter)
        if wealth_filter:
            members = members.filter(household__wealth_class=wealth_filter)
        if membership_type_filter:
            members = members.filter(membership_type=membership_type_filter)

        # Count members by status
        total_members = members.count()
        active = members.filter(membership_status=Member.MembershipStatus.ACTIVE).count()
        inactive = members.filter(membership_status=Member.MembershipStatus.INACTIVE).count()
        cancelled = members.filter(membership_status=Member.MembershipStatus.CANCELLED).count()

        # Count by membership type
        general = members.filter(membership_type=Member.MembershipType.GENERAL).count()
        lifetime = members.filter(membership_type=Member.MembershipType.LIFETIME).count()
        institutional = members.filter(membership_type=Member.MembershipType.INSTITUTIONAL).count()
        special = members.filter(membership_type=Member.MembershipType.SPECIAL).count()

        # Wealth distribution
        rich = members.filter(household__wealth_class=Household.WealthClass.RICH).count()
        medium = members.filter(household__wealth_class=Household.WealthClass.MEDIUM).count()
        poor = members.filter(household__wealth_class=Household.WealthClass.POOR).count()

        # Renewals
        renewals_qs = MembershipRenewal.objects.filter(member__in=members)
        total_renewals = renewals_qs.count()
        total_renewal_fees = renewals_qs.aggregate(Sum("fee_charged"))["fee_charged__sum"] or 0

        # Governance stats
        from apps.governance.models import Candidate, CommitteeMember

        committee_roles = CommitteeMember.objects.filter(member__in=members).count()
        candidacies = Candidate.objects.filter(member__in=members).count()

        # Billing stats
        from apps.billing.models import FeeCollection

        fee_collections = FeeCollection.objects.filter(member__in=members).count()
        collected_amount = (
            FeeCollection.objects.filter(member__in=members).aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        )

        # Harvest stats
        from apps.harvest.models import HarvestRequest

        harvest_requests = HarvestRequest.objects.filter(member__in=members).count()
        approved_harvest = HarvestRequest.objects.filter(member__in=members, status="approved").count()
        pending_harvest = HarvestRequest.objects.filter(member__in=members, status="pending").count()

        # Sales stats
        from apps.inventory.models import Sale

        sales = Sale.objects.filter(member__in=members).count()
        sales_amount = Sale.objects.filter(member__in=members).aggregate(Sum("total_amount"))["total_amount__sum"] or 0

        # Offense & Patrol stats
        from apps.offense.models import InformantReward, OffenseReport, PatrolLog

        offense_reports = OffenseReport.objects.filter(reported_by__in=members).count()
        informant_rewards = (
            InformantReward.objects.filter(informant__in=members).aggregate(Sum("reward_amount"))["reward_amount__sum"] or 0
        )
        patrol_logs = PatrolLog.objects.filter(watcher__in=members).count()

        # Livelihood stats
        from apps.livelihood.models import LivelihoodProgramRecord, RevolvingFundLoan

        households = Household.objects.filter(members__in=members).distinct()
        revolving_loans = RevolvingFundLoan.objects.filter(household__in=households).count()
        loan_amount = RevolvingFundLoan.objects.filter(household__in=households).aggregate(Sum("amount"))["amount__sum"] or 0
        livelihood_programs = LivelihoodProgramRecord.objects.filter(household__in=households).count()

        stats = {
            "total_members": total_members,
            "active_members": active,
            "inactive_members": inactive,
            "cancelled_members": cancelled,
            "general_members": general,
            "lifetime_members": lifetime,
            "institutional_members": institutional,
            "special_members": special,
            "rich_households": rich,
            "medium_households": medium,
            "poor_households": poor,
            "total_renewals": total_renewals,
            "total_renewal_fees": total_renewal_fees,
            "total_committee_roles": committee_roles,
            "total_candidacies": candidacies,
            "total_fee_collections": fee_collections,
            "total_collected_amount": collected_amount,
            "total_harvest_requests": harvest_requests,
            "approved_requests": approved_harvest,
            "pending_requests": pending_harvest,
            "total_sales": sales,
            "total_sales_amount": sales_amount,
            "total_offense_reports": offense_reports,
            "total_informant_rewards": informant_rewards,
            "total_patrol_logs": patrol_logs,
            "total_revolving_loans": revolving_loans,
            "total_loan_amount": loan_amount,
            "total_livelihood_programs": livelihood_programs,
        }

        serializer = MemberStatsAggregateSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_wealth_class(self, request):
        """Get member statistics grouped by household wealth class."""
        wealth_classes = Household.WealthClass.choices
        result = {}

        for value, label in wealth_classes:
            members = Member.objects.filter(household__wealth_class=value)
            result[value] = {
                "label": label,
                "count": members.count(),
                "active": members.filter(membership_status=Member.MembershipStatus.ACTIVE).count(),
                "inactive": members.filter(membership_status=Member.MembershipStatus.INACTIVE).count(),
                "cancelled": members.filter(membership_status=Member.MembershipStatus.CANCELLED).count(),
            }

        return Response(result)

    @action(detail=False, methods=["get"])
    def by_membership_type(self, request):
        """Get member statistics grouped by membership type."""
        membership_types = Member.MembershipType.choices
        result = {}

        for value, label in membership_types:
            members = Member.objects.filter(membership_type=value)
            result[value] = {
                "label": label,
                "count": members.count(),
                "active": members.filter(membership_status=Member.MembershipStatus.ACTIVE).count(),
                "inactive": members.filter(membership_status=Member.MembershipStatus.INACTIVE).count(),
                "cancelled": members.filter(membership_status=Member.MembershipStatus.CANCELLED).count(),
            }

        return Response(result)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        """Get member statistics grouped by membership status."""
        statuses = Member.MembershipStatus.choices
        result = {}

        for value, label in statuses:
            members = Member.objects.filter(membership_status=value)
            result[value] = {
                "label": label,
                "count": members.count(),
                "by_type": {
                    mtype: members.filter(membership_type=mtype).count() for mtype, _ in Member.MembershipType.choices
                },
            }

        return Response(result)


class UserMemberStatsViewSet(viewsets.ViewSet):
    """Provides statistics for users with member role."""

    permission_classes = [IsCommitteeOfficer | IsDFOViewer]

    @action(detail=False, methods=["get"])
    def aggregate(self, request):
        """Get aggregate statistics for member users."""
        # Get all member users
        member_users = User.objects.filter(role=User.Role.MEMBER)
        total = member_users.count()
        active = member_users.filter(is_active=True).count()
        inactive = member_users.filter(is_active=False).count()

        # Users with member profile
        with_profile = member_users.filter(member_profile__isnull=False).count()
        without_profile = member_users.filter(member_profile__isnull=True).count()

        # Users in households
        in_households = Member.objects.filter(user__in=member_users).count()

        # Users on committees
        from apps.governance.models import CommitteeMember

        on_committees = CommitteeMember.objects.filter(member__user__in=member_users).distinct().count()

        stats = {
            "total_member_users": total,
            "active_member_users": active,
            "inactive_member_users": inactive,
            "member_users_with_profile": with_profile,
            "member_users_without_profile": without_profile,
            "member_users_in_households": in_households,
            "member_users_on_committees": on_committees,
        }

        serializer = UserMemberStatsSerializer(stats)
        return Response(serializer.data)
