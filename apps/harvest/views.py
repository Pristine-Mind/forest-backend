from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.core.permissions import IsAuthenticatedReadOnly, IsCommitteeOfficer, IsMember
from apps.harvest.models import HarvestRequest
from apps.harvest.serializers import HarvestRequestSerializer


class HarvestRequestViewSet(viewsets.ModelViewSet):
    queryset = HarvestRequest.objects.select_related("member", "species", "approved_by")
    serializer_class = HarvestRequestSerializer
    permission_classes = [IsCommitteeOfficer | IsMember | IsAuthenticatedReadOnly]
    filterset_fields = ["source_type", "status", "species", "requested_date"]
    search_fields = ["member__full_name", "species__species_name", "operation_name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_committee_officer() or user.is_dfo_viewer():
            return self.queryset
        if user.is_member_user():
            member = getattr(user, "member_profile", None)
            if member is None:
                return self.queryset.none()
            return self.queryset.filter(member=member)
        return self.queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_member_user():
            member = getattr(user, "member_profile", None)
            if member is None:
                raise PermissionDenied("User is not linked to a member profile.")
            serializer.save(member=member, user=user)
        else:
            serializer.save(user=user)

    @action(detail=True, methods=["post"], permission_classes=[IsCommitteeOfficer])
    def approve(self, request, pk=None):
        from apps.core.services import approve_harvest_request

        harvest_request = self.get_object()
        if harvest_request.status != HarvestRequest.Status.PENDING:
            raise ValidationError("Only pending requests can be approved.")

        try:
            approve_harvest_request(harvest_request, request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))

        return Response({"status": "approved"})

    @action(detail=True, methods=["post"], permission_classes=[IsCommitteeOfficer])
    def reject(self, request, pk=None):
        harvest_request = self.get_object()
        if harvest_request.status != HarvestRequest.Status.PENDING:
            raise ValidationError("Only pending requests can be rejected.")

        notes = request.data.get("notes", "").strip()
        if not notes:
            raise ValidationError({"notes": "Notes are required when rejecting a request."})

        harvest_request.status = HarvestRequest.Status.REJECTED
        harvest_request.approved_by = request.user
        harvest_request.notes = notes
        harvest_request.save(user=request.user)

        return Response({"status": "rejected"})
