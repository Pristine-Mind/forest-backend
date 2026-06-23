from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsCommitteeOfficer,
    IsMember,
    IsSubCommitteeMember,
)
from apps.offense.models import (
    EvidenceItem,
    HearingRecord,
    InformantReward,
    OffenseReport,
    PatrolLog,
)
from apps.offense.serializers import (
    EvidenceItemSerializer,
    HearingRecordSerializer,
    InformantRewardSerializer,
    OffenseReportSerializer,
    PatrolLogSerializer,
)


def _is_offense_subcommittee_user(user):
    from apps.governance.models import CommitteeMember, SubCommittee

    if not user.is_sub_committee_user():
        return False
    member = getattr(user, "member_profile", None)
    if not member:
        return False
    cm = CommitteeMember.objects.filter(member=member, status=CommitteeMember.Status.ACTIVE).first()
    if not cm:
        return False
    return cm.subcommittees.filter(name__in=[SubCommittee.Name.DISPUTE_RESOLUTION, SubCommittee.Name.ANTI_POACHING]).exists()


class OffenseReportViewSet(viewsets.ModelViewSet):
    queryset = OffenseReport.objects.prefetch_related("evidence", "hearings")
    serializer_class = OffenseReportSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["status", "offense_type", "report_date"]
    search_fields = ["accused_name", "offense_type"]

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_member_user():
            member = getattr(user, "member_profile", None)
            if member is None:
                raise PermissionDenied("User is not linked to a member profile.")
            serializer.save(reported_by=member, user=user)
        else:
            serializer.save(user=user)

    @action(detail=True, methods=["post"], permission_classes=[IsCommitteeOfficer])
    def resolve(self, request, pk=None):
        from apps.core.services import resolve_offense_fine_paid

        offense = self.get_object()
        informant_id = request.data.get("informant_id")
        resolution = request.data.get("resolution")

        if resolution not in [
            OffenseReport.Resolution.FINE_PAID,
            OffenseReport.Resolution.ESCALATED,
            OffenseReport.Resolution.DISMISSED,
        ]:
            raise ValidationError({"resolution": "Invalid resolution value."})

        try:
            resolve_offense_fine_paid(offense, informant_id, request.user, resolution=resolution)
        except ValueError as exc:
            raise ValidationError(str(exc))

        return Response(OffenseReportSerializer(offense).data)


class EvidenceItemViewSet(viewsets.ModelViewSet):
    queryset = EvidenceItem.objects.select_related("offense")
    serializer_class = EvidenceItemSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["offense", "item_type"]


class HearingRecordViewSet(viewsets.ModelViewSet):
    queryset = HearingRecord.objects.select_related("offense")
    serializer_class = HearingRecordSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["offense", "hearing_date"]


class InformantRewardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InformantReward.objects.select_related("offense", "informant")
    serializer_class = InformantRewardSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["offense", "informant"]


class PatrolLogViewSet(viewsets.ModelViewSet):
    queryset = PatrolLog.objects.select_related("watcher", "offense")
    serializer_class = PatrolLogSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["watcher", "patrol_date"]
