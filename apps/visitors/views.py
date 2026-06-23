from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.permissions import IsAuthenticatedReadOnly, IsCommitteeOfficer
from apps.visitors.models import OfficialGuestLog, VisitorEntry, VisitorFeeRate
from apps.visitors.serializers import (
    OfficialGuestLogSerializer,
    VisitorEntrySerializer,
    VisitorFeeRateSerializer,
)


class VisitorFeeRateViewSet(viewsets.ModelViewSet):
    queryset = VisitorFeeRate.objects.all()
    serializer_class = VisitorFeeRateSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]


class VisitorEntryViewSet(viewsets.ModelViewSet):
    queryset = VisitorEntry.objects.all()
    serializer_class = VisitorEntrySerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["entry_date", "visit_purpose", "fee_waived"]

    @action(detail=False, methods=["post"], permission_classes=[IsCommitteeOfficer])
    def log_and_collect(self, request):
        from apps.core.services import record_visitor_entry

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            entry = record_visitor_entry(serializer.validated_data, request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))

        return Response(VisitorEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class OfficialGuestLogViewSet(viewsets.ModelViewSet):
    queryset = OfficialGuestLog.objects.all()
    serializer_class = OfficialGuestLogSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["visit_start_date", "visit_end_date"]
    search_fields = ["visitor_name", "designation"]
