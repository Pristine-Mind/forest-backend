import pytest
from django.core.files.storage import default_storage

from apps.billing.models import Receipt
from apps.billing.tasks import generate_receipt_pdf_task
from apps.core.models import User


@pytest.mark.django_db
def test_generate_receipt_pdf_task_creates_pdf():
    user = User.objects.create_user(email="issuer@example.com", password="testpass123")
    receipt = Receipt.objects.create(
        reference_type=Receipt.ReferenceType.SALE,
        reference_id=1,
        amount=1000,
        issued_date="2026-06-15",
        issued_by=user,
    )

    assert not receipt.pdf_file

    result = generate_receipt_pdf_task.apply(args=[receipt.receipt_no])

    assert result.successful()
    receipt.refresh_from_db()
    assert receipt.pdf_file
    assert receipt.pdf_file.name.endswith(".pdf")
    assert default_storage.exists(receipt.pdf_file.name)
