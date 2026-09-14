from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Case, When, Value, CharField

from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsChair,
    IsCommitteeChair,
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
from apps.members.models import Household, Member


class CommitteeMemberViewSet(viewsets.ModelViewSet):
    queryset = CommitteeMember.objects.prefetch_related("subcommittees")
    serializer_class = CommitteeMemberSerializer
    permission_classes = [IsCommitteeChair | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["position", "status", "term_start", "term_end"]
    search_fields = ["member_object__household_head_name", "member_object__full_name", "position"]

    def get_queryset(self):
        """
        Order committee members by position hierarchy:
        chair, vice_chair, secretary, joint_secretary, treasurer, member
        """
        queryset = super().get_queryset()
        
        position_order = Case(
            When(position='chair', then=Value(0)),
            When(position='vice_chair', then=Value(1)),
            When(position='secretary', then=Value(2)),
            When(position='joint_secretary', then=Value(3)),
            When(position='treasurer', then=Value(4)),
            When(position='member', then=Value(5)),
            output_field=CharField(),
        )
        
        return queryset.annotate(position_order=position_order).order_by('position_order', '-term_start')

    def get_permissions(self):
        """
        Override to enforce chair-only permissions for add/edit operations.
        Only users with the Chair role can create, update, or delete committee members.
        """
        if self.request.method not in ["GET", "HEAD", "OPTIONS"]:
            # Write operations (POST, PUT, PATCH, DELETE) require IsChair permission
            return [IsChair()]
        # Read operations allow broader audience
        return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=["get"])
    def search_members(self, request):
        """
        Search for members across both Household and Member models.
        Query parameters:
        - q: search query (searches english_name and member full_name_en)
        - type: 'household' | 'member' | 'all' (default: 'all')
        - limit: max results (default: 10)
        """
        query = request.query_params.get("q", "").strip()
        member_type = request.query_params.get("type", "all")
        limit = int(request.query_params.get("limit", 10))

        results = []

        if member_type in ["household", "all"]:
            households = Household.objects.filter(english_name__icontains=query)[:limit]
            results.extend(
                [
                    {
                        "id": h.id,
                        "name": h.english_name,
                        "type": "household",
                        "content_type": "household",
                        "object_id": h.id,
                        "tole": h.tole,
                    }
                    for h in households
                ]
            )

        if member_type in ["member", "all"]:
            members = Member.objects.filter(full_name_en__icontains=query).select_related("household")[:limit]
            results.extend(
                [
                    {
                        "id": m.id,
                        "name": m.full_name_en,
                        "type": "member",
                        "content_type": "member",
                        "object_id": m.id,
                        "household_name": m.household.english_name,
                    }
                    for m in members
                ]
            )

        return Response(results)

    @action(detail=False, methods=["get"])
    def quota_status(self, request):
        from apps.governance.signals import check_committee_composition_quota

        return Response(check_committee_composition_quota())


class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.prefetch_related("candidates__member")
    serializer_class = ElectionSerializer
    permission_classes = [IsCommitteeChair | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["status", "election_date"]


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.select_related("member", "election")
    serializer_class = CandidateSerializer
    permission_classes = [IsCommitteeChair | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["election", "result"]


class SubCommitteeViewSet(viewsets.ModelViewSet):
    queryset = SubCommittee.objects.prefetch_related("committee_members")
    serializer_class = SubCommitteeSerializer
    permission_classes = [IsCommitteeChair | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_sub_committee_user():
            member = getattr(user, "member_profile", None)
            if member:
                # Get CommitteeMember records for this user where content_type is Member
                member_ct = ContentType.objects.get_for_model(Member)
                committee_member = CommitteeMember.objects.filter(
                    content_type=member_ct, object_id=member.id, status=CommitteeMember.Status.ACTIVE
                ).first()
                if committee_member:
                    return self.queryset.filter(committee_members=committee_member)
        return self.queryset


class OathRecordViewSet(viewsets.ModelViewSet):
    queryset = OathRecord.objects.select_related("committee_member")
    serializer_class = OathRecordSerializer
    permission_classes = [IsCommitteeChair | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["oath_date"]


class NoConfidenceMotionViewSet(viewsets.ModelViewSet):
    queryset = NoConfidenceMotion.objects.select_related("target_committee_member")
    serializer_class = NoConfidenceMotionSerializer
    permission_classes = [IsCommitteeChair | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["target_type", "assembly_decision"]


class HandoverRecordViewSet(viewsets.ModelViewSet):
    queryset = HandoverRecord.objects.select_related(
        "outgoing_committee_member__member", "incoming_committee_member__member"
    )
    serializer_class = HandoverRecordSerializer
    permission_classes = [IsCommitteeChair]
    filterset_fields = ["status", "deadline_date"]
