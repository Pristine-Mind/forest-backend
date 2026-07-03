from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.core.permissions import (
    IsCommitteeOfficer,
    IsDFOViewer,
    IsMember,
    IsSubCommitteeMember,
)
from apps.members.models import Household, Member, MembershipRenewal
from apps.members.serializers import (
    HouseholdSerializer,
    MemberListSerializer,
    MemberSerializer,
    MembershipRenewalSerializer,
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
    filterset_fields = ["membership_type", "membership_status", "household__wealth_class"]
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
