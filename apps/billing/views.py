from django.http import FileResponse, HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.billing.models import FeeCollection, Receipt
from apps.billing.serializers import FeeCollectionSerializer, ReceiptSerializer
from apps.billing.tasks import generate_receipt_pdf_task
from apps.core.permissions import IsAuthenticatedReadOnly, IsCommitteeOfficer


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["reference_type", "issued_date"]
    search_fields = ["receipt_no"]
    lookup_field = "receipt_no"

    @action(detail=True, methods=["get"], url_path="download")
    def download_pdf(self, request, receipt_no=None):
        receipt = self.get_object()
        if not receipt.pdf_file:
            return Response(
                {"detail": "PDF not generated yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return FileResponse(
            receipt.pdf_file.open(),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"{receipt.receipt_no}.pdf",
        )

    @action(detail=True, methods=["post"], url_path="regenerate")
    def regenerate_pdf(self, request, receipt_no=None):
        receipt = self.get_object()
        generate_receipt_pdf_task.delay(receipt.receipt_no)
        return Response({"status": "queued"})


class FeeCollectionViewSet(viewsets.ModelViewSet):
    queryset = FeeCollection.objects.select_related("member")
    serializer_class = FeeCollectionSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["fee_type", "payment_status", "member"]
    search_fields = ["member__full_name", "member__citizenship_no"]
