from datetime import date

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
    search_fields = ["member__full_name", "member__household__citizenship_no"]

    def get_serializer_context(self):
        """Add request to serializer context for user info in receipt generation."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(detail=True, methods=["post"], url_path="generate-receipt")
    def generate_receipt(self, request, pk=None):
        """Generate receipt for a fee collection if payment is recorded."""
        fee_collection = self.get_object()

        if fee_collection.amount_paid <= 0:
            return Response(
                {"detail": "No payment recorded for this fee collection."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if fee_collection.receipt_no:
            return Response(
                {"detail": f"Receipt {fee_collection.receipt_no.receipt_no} already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            receipt = Receipt.objects.create(
                reference_type=Receipt.ReferenceType.FEE_COLLECTION,
                reference_id=fee_collection.id,
                amount=fee_collection.amount_paid,
                issued_date=date.today(),
                issued_by=request.user,
            )
            fee_collection.receipt_no = receipt
            fee_collection.save(update_fields=["receipt_no"])

            # Trigger PDF generation
            generate_receipt_pdf_task.delay(receipt.receipt_no)

            return Response(
                {
                    "receipt_no": receipt.receipt_no,
                    "status": "created",
                    "message": "Receipt created and PDF generation queued.",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"detail": f"Error creating receipt: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="bulk-generate-receipts")
    def bulk_generate_receipts(self, request):
        """Generate receipts for multiple fee collections in bulk."""
        fee_ids = request.data.get("fee_ids", [])

        if not fee_ids:
            return Response(
                {"detail": "fee_ids list is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_receipts = []
        errors = []

        for fee_id in fee_ids:
            try:
                fee_collection = FeeCollection.objects.get(id=fee_id)

                if fee_collection.amount_paid <= 0:
                    errors.append(f"Fee {fee_id}: No payment recorded")
                    continue

                if fee_collection.receipt_no:
                    errors.append(f"Fee {fee_id}: Receipt already exists")
                    continue

                receipt = Receipt.objects.create(
                    reference_type=Receipt.ReferenceType.FEE_COLLECTION,
                    reference_id=fee_collection.id,
                    amount=fee_collection.amount_paid,
                    issued_date=date.today(),
                    issued_by=request.user,
                )
                fee_collection.receipt_no = receipt
                fee_collection.save(update_fields=["receipt_no"])

                # Trigger PDF generation
                generate_receipt_pdf_task.delay(receipt.receipt_no)

                created_receipts.append(
                    {
                        "fee_id": fee_id,
                        "receipt_no": receipt.receipt_no,
                    }
                )
            except FeeCollection.DoesNotExist:
                errors.append(f"Fee {fee_id}: Not found")
            except Exception as e:
                errors.append(f"Fee {fee_id}: {str(e)}")

        return Response(
            {
                "created": len(created_receipts),
                "receipts": created_receipts,
                "errors": errors,
            },
            status=status.HTTP_201_CREATED if created_receipts else status.HTTP_400_BAD_REQUEST,
        )
