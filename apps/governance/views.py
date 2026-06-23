from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsCommitteeOfficer,
    IsMember,
    IsSubCommitteeMember,
)
from apps.governance.models import (
    Candidate,
    CommitteeMember,
    Election,
    HandoverRecord,
    NoConfidenceMotion,
    OathRecord,
    SubCommittee,
)
from apps.governance.serializers import (
    CandidateSerializer,
    CommitteeMemberSerializer,
    ElectionSerializer,
    HandoverRecordSerializer,
    NoConfidenceMotionSerializer,
    OathRecordSerializer,
    SubCommitteeSerializer,
)


class CommitteeMemberViewSet(viewsets.ModelViewSet):
    queryset = CommitteeMember.objects.select_related("member").prefetch_related("subcommittees")
    serializer_class = CommitteeMemberSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["position", "status", "term_start", "term_end"]
    search_fields = ["member__full_name", "position"]

    @action(detail=False, methods=["get"])
    def quota_status(self, request):
        from apps.governance.signals import check_committee_composition_quota

        return Response(check_committee_composition_quota())


class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.prefetch_related("candidates__member")
    serializer_class = ElectionSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["status", "election_date"]


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.select_related("member", "election")
    serializer_class = CandidateSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["election", "result"]


class SubCommitteeViewSet(viewsets.ModelViewSet):
    queryset = SubCommittee.objects.prefetch_related("committee_members__member")
    serializer_class = SubCommitteeSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_sub_committee_user():
            member = getattr(user, "member_profile", None)
            if member:
                committee_member = CommitteeMember.objects.filter(
                    member=member, status=CommitteeMember.Status.ACTIVE
                ).first()
                if committee_member:
                    return self.queryset.filter(committee_members=committee_member)
        return self.queryset


class OathRecordViewSet(viewsets.ModelViewSet):
    queryset = OathRecord.objects.select_related("committee_member__member")
    serializer_class = OathRecordSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["oath_date"]


class NoConfidenceMotionViewSet(viewsets.ModelViewSet):
    queryset = NoConfidenceMotion.objects.select_related("target_committee_member__member")
    serializer_class = NoConfidenceMotionSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["target_type", "assembly_decision"]


class HandoverRecordViewSet(viewsets.ModelViewSet):
    queryset = HandoverRecord.objects.select_related(
        "outgoing_committee_member__member", "incoming_committee_member__member"
    )
    serializer_class = HandoverRecordSerializer
    permission_classes = [IsCommitteeOfficer]
    filterset_fields = ["status", "deadline_date"]
