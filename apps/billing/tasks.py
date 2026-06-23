from celery import shared_task
from django.core.files.base import ContentFile

from apps.billing.models import Receipt
from apps.billing.pdf import generate_receipt_pdf


@shared_task
def generate_receipt_pdf_task(receipt_no):
    """Generate and store a PDF receipt asynchronously."""

    try:
        receipt = Receipt.objects.get(receipt_no=receipt_no)
    except Receipt.DoesNotExist:
        return f"Receipt {receipt_no} not found"

    if receipt.pdf_file:
        return f"Receipt {receipt_no} already has a PDF"

    buffer = generate_receipt_pdf(receipt)
    filename = f"{receipt.receipt_no}.pdf"
    receipt.pdf_file.save(filename, ContentFile(buffer.read()), save=True)
    return f"Generated PDF for {receipt_no}"
