from celery import shared_task
from django.core.files.base import ContentFile

from apps.billing.models import Receipt


@shared_task
def generate_receipt_pdf_task(receipt_no):
    """Generate and store a PDF receipt asynchronously.

    Uses WeasyPrint if available (better Devanagari support),
    otherwise falls back to ReportLab.
    """

    try:
        receipt = Receipt.objects.get(receipt_no=receipt_no)
    except Receipt.DoesNotExist:
        return f"Receipt {receipt_no} not found"

    if receipt.pdf_file:
        return f"Receipt {receipt_no} already has a PDF"

    try:
        # Try WeasyPrint first (better complex script support)
        try:
            from apps.billing.pdf_weasyprint import generate_receipt_pdf_weasyprint

            buffer = generate_receipt_pdf_weasyprint(receipt)
            print(f"✓ Generated PDF using WeasyPrint for {receipt_no}")
        except ImportError:
            # Fall back to ReportLab
            from apps.billing.pdf import generate_receipt_pdf

            buffer = generate_receipt_pdf(receipt)
            print(f"✓ Generated PDF using ReportLab for {receipt_no}")

        filename = f"{receipt.receipt_no}.pdf"
        receipt.pdf_file.save(filename, ContentFile(buffer.read()), save=True)
        return f"Generated PDF for {receipt_no}"
    except Exception as e:
        print(f"✗ Error generating PDF for receipt {receipt_no}: {e}")
        import traceback

        traceback.print_exc()
        raise
