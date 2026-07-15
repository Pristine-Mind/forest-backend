from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.permissions import IsAuthenticatedReadOnly, IsCommitteeOfficer
from apps.inventory.models import PriceRate, Sale, StockLedger, StockTransaction, TimberLogEntry
from apps.inventory.serializers import (
    PriceRateSerializer,
    SaleSerializer,
    StockLedgerSerializer,
    StockTransactionSerializer,
    TimberLogEntrySerializer,
)


class StockLedgerViewSet(viewsets.ModelViewSet):
    queryset = StockLedger.objects.select_related("species")
    serializer_class = StockLedgerSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["species", "grade"]
    search_fields = ["species__species_name", "grade"]


class StockTransactionViewSet(viewsets.ModelViewSet):
    queryset = StockTransaction.objects.select_related("stock")
    serializer_class = StockTransactionSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["stock", "transaction_type", "reference_type"]

    @action(detail=False, methods=["post"], permission_classes=[IsCommitteeOfficer])
    def record_adjustment(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save(reference_type=StockTransaction.ReferenceType.ADJUSTMENT, reference_id=0)
        return Response(self.get_serializer(transaction).data, status=status.HTTP_201_CREATED)


class PriceRateViewSet(viewsets.ModelViewSet):
    queryset = PriceRate.objects.select_related("species")
    serializer_class = PriceRateSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["species", "grade", "buyer_type"]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related("species", "member")
    serializer_class = SaleSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["buyer_type", "species", "grade", "payment_status"]
    search_fields = ["buyer_name", "member__full_name"]

    @action(detail=False, methods=["post"], permission_classes=[IsCommitteeOfficer])
    def record(self, request):
        from apps.core.services import record_sale

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.errors)
        try:
            sale = record_sale(serializer.validated_data, request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class TimberLogEntryViewSet(viewsets.ModelViewSet):
    queryset = TimberLogEntry.objects.select_related("species").all()
    serializer_class = TimberLogEntrySerializer
    filterset_fields = ["species", "grade"]
    search_fields = ["tree_no", "tree_golia_no", "golia_no"]
    ordering = ["-created_at"]
