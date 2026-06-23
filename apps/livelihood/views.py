from rest_framework import viewsets

from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsCommitteeOfficer,
    IsMember,
    IsSubCommitteeMember,
)
from apps.livelihood.models import (
    LivelihoodProgramRecord,
    PovertyGroupAgreement,
    RevolvingFundLoan,
)
from apps.livelihood.serializers import (
    LivelihoodProgramRecordSerializer,
    PovertyGroupAgreementSerializer,
    RevolvingFundLoanSerializer,
)


def _household_for_user(user):
    member = getattr(user, "member_profile", None)
    return member.household if member else None


class RevolvingFundLoanViewSet(viewsets.ModelViewSet):
    queryset = RevolvingFundLoan.objects.select_related("household")
    serializer_class = RevolvingFundLoanSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsMember | IsAuthenticatedReadOnly]
    filterset_fields = ["status", "issue_date"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_officer() or user.is_dfo_viewer() or user.is_sub_committee_user():
            return self.queryset
        household = _household_for_user(user)
        if household:
            return self.queryset.filter(household=household)
        return self.queryset.none()


class LivelihoodProgramRecordViewSet(viewsets.ModelViewSet):
    queryset = LivelihoodProgramRecord.objects.select_related("household")
    serializer_class = LivelihoodProgramRecordSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsMember | IsAuthenticatedReadOnly]
    filterset_fields = ["program_type", "program_date"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_officer() or user.is_dfo_viewer() or user.is_sub_committee_user():
            return self.queryset
        household = _household_for_user(user)
        if household:
            return self.queryset.filter(household=household)
        return self.queryset.none()


class PovertyGroupAgreementViewSet(viewsets.ModelViewSet):
    queryset = PovertyGroupAgreement.objects.all()
    serializer_class = PovertyGroupAgreementSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsMember | IsAuthenticatedReadOnly]
    filterset_fields = ["status"]
    search_fields = ["subgroup_name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_officer() or user.is_dfo_viewer() or user.is_sub_committee_user():
            return self.queryset
        household = _household_for_user(user)
        if household:
            return self.queryset.filter(member_households__contains=household.pk)
        return self.queryset.none()
