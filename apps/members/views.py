from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.models import Notification, SystemConfig, User
from apps.core.permissions import (
    IsCommitteeChair,
    IsDFOViewer,
    IsMember,
    IsSubCommitteeMember,
)
from apps.members.models import Household, Member, MembershipRenewal
from apps.members.serializers import (
    HouseholdDetailStatsSerializer,
    HouseholdSerializer,
    HouseholdStatsAggregateSerializer,
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
    queryset = Household.objects.order_by("english_name")
    serializer_class = HouseholdSerializer
    permission_classes = [IsCommitteeChair | IsMember | IsSubCommitteeMember | IsDFOViewer]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["wealth_class", "tole", "status"]
    search_fields = ["household_head_name", "tole", "english_name", "citizenship_no"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_chair() or user.is_dfo_viewer():
            return self.queryset
        return self.queryset.filter(_member_filter_for_user(user))

    def perform_create(self, serializer):
        with transaction.atomic():
            household = serializer.save(created_by=self.request.user, updated_by=self.request.user)
            if not self.request.user.is_staff_user():
                return

            household.approval_status = Household.ApprovalStatus.PENDING
            household.save(update_fields=["approval_status", "updated_at"])

            description = (
                f"{self.request.user.full_name} requested to add a new member "
                f"for the household {household.household_head_name}."
            )
            for chair in User.objects.filter(role=User.Role.COMMITTEE_CHAIR):
                Notification.objects.create(
                    created_by=self.request.user,
                    updated_by=self.request.user,
                    recipient=chair,
                    notification_type=Notification.Type.MEMBER_REQUEST,
                    title=f"New Member Request: {household.household_head_name}",
                    description=description,
                    action_required=True,
                    content_type="Household",
                    object_id=household.pk,
                )

    @action(detail=True, methods=["post"], permission_classes=[IsCommitteeChair])
    def approve(self, request, pk=None):
        with transaction.atomic():
            household = self._get_locked_household(request, pk)
            if household.approval_status != Household.ApprovalStatus.PENDING:
                return Response(
                    {
                        "detail": (
                            "Can only approve pending household requests. "
                            f"Current status: {household.approval_status}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            household.approval_status = Household.ApprovalStatus.APPROVED
            household.approved_by = request.user
            household.approved_at = timezone.now()
            household.rejection_reason = ""
            household.save(
                user=request.user,
                update_fields=[
                    "approval_status",
                    "approved_by",
                    "approved_at",
                    "rejection_reason",
                    "updated_by",
                    "updated_at",
                ],
            )
            self._action_request_notifications(household, request.user, "Household request accepted.")

        return Response(self.get_serializer(household).data)

    @action(detail=True, methods=["post"], permission_classes=[IsCommitteeChair])
    def reject(self, request, pk=None):
        rejection_reason = request.data.get("rejection_reason", "No reason provided")
        with transaction.atomic():
            household = self._get_locked_household(request, pk)
            if household.approval_status != Household.ApprovalStatus.PENDING:
                return Response(
                    {
                        "detail": (
                            "Can only reject pending household requests. "
                            f"Current status: {household.approval_status}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            household.approval_status = Household.ApprovalStatus.REJECTED
            household.rejection_reason = rejection_reason
            household.save(
                user=request.user,
                update_fields=["approval_status", "rejection_reason", "updated_by", "updated_at"],
            )
            self._action_request_notifications(
                household,
                request.user,
                f"Household request rejected: {rejection_reason}",
            )

        return Response(self.get_serializer(household).data)

    def _get_locked_household(self, request, pk):
        queryset = self.filter_queryset(self.get_queryset()).select_for_update()
        household = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, household)
        return household

    @staticmethod
    def _action_request_notifications(household, actioned_by, action_notes):
        notifications = Notification.objects.filter(
            content_type="Household",
            object_id=household.pk,
            notification_type=Notification.Type.MEMBER_REQUEST,
            status__in=[Notification.Status.UNREAD, Notification.Status.READ],
        )
        for notification in notifications:
            notification.mark_as_actioned(actioned_by, action_notes)

    def perform_update(self, serializer):
        serializer.save()


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.select_related("household", "user")
    serializer_class = MemberSerializer
    permission_classes = [IsCommitteeChair | IsMember | IsSubCommitteeMember | IsDFOViewer]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["household", "household__wealth_class", "household__membership_type", "household__membership_status"]
    search_fields = ["full_name", "household__citizenship_no"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_chair() or user.is_dfo_viewer():
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
    permission_classes = [IsCommitteeChair]
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
    permission_classes = [IsCommitteeChair | IsDFOViewer]
    filterset_fields = ["household__membership_type", "household__membership_status", "household__wealth_class", "household"]
    search_fields = ["full_name", "household__citizenship_no"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_chair() or user.is_dfo_viewer():
            return self.queryset
        return self.queryset.none()


class HouseholdDetailStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides detailed household statistics with aggregated member data."""

    queryset = Household.objects.prefetch_related("members").all()
    serializer_class = HouseholdDetailStatsSerializer
    permission_classes = [IsCommitteeChair | IsDFOViewer]
    filterset_fields = ["wealth_class", "status", "membership_type", "membership_status"]
    search_fields = ["household_head_name", "tole", "citizenship_no"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_chair() or user.is_dfo_viewer():
            return self.queryset
        if user.is_member_user() or user.is_sub_committee_user():
            member = getattr(user, "member_profile", None)
            if member is None:
                return self.queryset.none()
            return self.queryset.filter(pk=member.household_id)
        return self.queryset.none()


class HouseholdStatsViewSet(viewsets.ViewSet):
    """Provides aggregate statistics across households with member data aggregation."""

    permission_classes = [IsCommitteeChair | IsDFOViewer]

    @action(detail=False, methods=["get"])
    def aggregate(self, request):
        """Get aggregate statistics across all or filtered households."""
        # Get base queryset
        households = Household.objects.prefetch_related("members")

        # Apply filters
        status_filter = request.query_params.get("status", None)
        wealth_filter = request.query_params.get("wealth_class", None)
        membership_type_filter = request.query_params.get("membership_type", None)
        membership_status_filter = request.query_params.get("membership_status", None)

        if status_filter:
            households = households.filter(status=status_filter)
        if wealth_filter:
            households = households.filter(wealth_class=wealth_filter)
        if membership_type_filter:
            households = households.filter(membership_type=membership_type_filter)
        if membership_status_filter:
            households = households.filter(membership_status=membership_status_filter)

        # Count households
        total_households = households.count()
        active_households = households.filter(status=Household.Status.ACTIVE).count()
        inactive_households = households.filter(status=Household.Status.INACTIVE).count()

        # Membership types distribution
        general = households.filter(membership_type=Household.MembershipType.GENERAL).count()
        lifetime = households.filter(membership_type=Household.MembershipType.LIFETIME).count()
        institutional = households.filter(membership_type=Household.MembershipType.INSTITUTIONAL).count()
        special = households.filter(membership_type=Household.MembershipType.SPECIAL).count()

        # Membership status distribution
        active_memberships = households.filter(membership_status=Household.MembershipStatus.ACTIVE).count()
        inactive_memberships = households.filter(membership_status=Household.MembershipStatus.INACTIVE).count()
        cancelled_memberships = households.filter(membership_status=Household.MembershipStatus.CANCELLED).count()

        # Wealth distribution
        rich = households.filter(wealth_class=Household.WealthClass.RICH).count()
        medium = households.filter(wealth_class=Household.WealthClass.MEDIUM).count()
        poor = households.filter(wealth_class=Household.WealthClass.POOR).count()

        # Member counts
        total_members = Member.objects.filter(household__in=households).count()
        avg_members = total_members / total_households if total_households > 0 else 0

        # Renewals (aggregated from all members in households)
        renewals_qs = MembershipRenewal.objects.filter(member__household__in=households)
        total_renewals = renewals_qs.count()
        total_renewal_fees = renewals_qs.aggregate(Sum("fee_charged"))["fee_charged__sum"] or 0

        # Governance stats
        from apps.governance.models import Candidate, CommitteeMember

        committee_roles = CommitteeMember.objects.filter(member__household__in=households).count()
        candidacies = Candidate.objects.filter(member__household__in=households).count()

        # Billing stats
        from apps.billing.models import FeeCollection

        fee_collections = FeeCollection.objects.filter(member__household__in=households).count()
        collected_amount = (
            FeeCollection.objects.filter(member__household__in=households).aggregate(Sum("amount_paid"))["amount_paid__sum"]
            or 0
        )

        # Harvest stats
        from apps.harvest.models import HarvestRequest

        harvest_requests = HarvestRequest.objects.filter(member__household__in=households).count()
        approved_harvest = HarvestRequest.objects.filter(member__household__in=households, status="approved").count()
        pending_harvest = HarvestRequest.objects.filter(member__household__in=households, status="pending").count()

        # Sales stats
        from apps.inventory.models import Sale

        sales = Sale.objects.filter(member__household__in=households).count()
        sales_amount = (
            Sale.objects.filter(member__household__in=households).aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        )

        # Offense & Patrol stats
        from apps.offense.models import InformantReward, OffenseReport, PatrolLog

        offense_reports = OffenseReport.objects.filter(reported_by__household__in=households).count()
        informant_rewards = (
            InformantReward.objects.filter(informant__household__in=households).aggregate(Sum("reward_amount"))[
                "reward_amount__sum"
            ]
            or 0
        )
        patrol_logs = PatrolLog.objects.filter(watcher__household__in=households).count()

        # Livelihood stats
        from apps.livelihood.models import LivelihoodProgramRecord, RevolvingFundLoan

        revolving_loans = RevolvingFundLoan.objects.filter(household__in=households).count()
        loan_amount = RevolvingFundLoan.objects.filter(household__in=households).aggregate(Sum("amount"))["amount__sum"] or 0
        livelihood_programs = LivelihoodProgramRecord.objects.filter(household__in=households).count()

        stats = {
            "total_households": total_households,
            "active_households": active_households,
            "inactive_households": inactive_households,
            "general_households": general,
            "lifetime_households": lifetime,
            "institutional_households": institutional,
            "special_households": special,
            "active_memberships": active_memberships,
            "inactive_memberships": inactive_memberships,
            "cancelled_memberships": cancelled_memberships,
            "rich_households": rich,
            "medium_households": medium,
            "poor_households": poor,
            "total_members": total_members,
            "avg_members_per_household": avg_members,
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

        serializer = HouseholdStatsAggregateSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_wealth_class(self, request):
        """Get household statistics grouped by wealth class."""
        wealth_classes = Household.WealthClass.choices
        result = {}

        for value, label in wealth_classes:
            households = Household.objects.filter(wealth_class=value)
            members_in_class = Member.objects.filter(household__in=households)
            result[value] = {
                "label": label,
                "household_count": households.count(),
                "total_members": members_in_class.count(),
                "active_households": households.filter(status=Household.Status.ACTIVE).count(),
                "inactive_households": households.filter(status=Household.Status.INACTIVE).count(),
            }

        return Response(result)

    @action(detail=False, methods=["get"])
    def by_membership_type(self, request):
        """Get household statistics grouped by membership type."""
        membership_types = Household.MembershipType.choices
        result = {}

        for value, label in membership_types:
            households = Household.objects.filter(membership_type=value)
            members_in_type = Member.objects.filter(household__in=households)
            result[value] = {
                "label": label,
                "household_count": households.count(),
                "total_members": members_in_type.count(),
                "active": households.filter(membership_status=Household.MembershipStatus.ACTIVE).count(),
                "inactive": households.filter(membership_status=Household.MembershipStatus.INACTIVE).count(),
                "cancelled": households.filter(membership_status=Household.MembershipStatus.CANCELLED).count(),
            }

        return Response(result)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        """Get household statistics grouped by membership status."""
        statuses = Household.MembershipStatus.choices
        result = {}

        for value, label in statuses:
            households = Household.objects.filter(membership_status=value)
            members_in_status = Member.objects.filter(household__in=households)
            result[value] = {
                "label": label,
                "household_count": households.count(),
                "total_members": members_in_status.count(),
                "by_type": {
                    mtype: households.filter(membership_type=mtype).count() for mtype, _ in Household.MembershipType.choices
                },
            }

        return Response(result)


class UserMemberStatsViewSet(viewsets.ViewSet):
    """Provides statistics for users with member role."""

    permission_classes = [IsCommitteeChair | IsDFOViewer]

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
