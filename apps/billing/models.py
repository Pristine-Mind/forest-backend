from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel, ReceiptSequence


ONES = ["", "एक", "दुई", "तीन", "चार", "पाँच", "छ", "सात", "आठ", "नौ"]

NUM_WORDS_0_99 = [
    "शून्य",
    "एक",
    "दुई",
    "तीन",
    "चार",
    "पाँच",
    "छ",
    "सात",
    "आठ",
    "नौ",
    "दस",
    "एघार",
    "बाह्र",
    "तेह्र",
    "चौध",
    "पन्ध्र",
    "सोह्र",
    "सत्र",
    "अठार",
    "उन्नाइस",
    "बीस",
    "एक्काइस",
    "बाइस",
    "तेइस",
    "चौबिस",
    "पच्चीस",
    "छब्बिस",
    "सत्ताइस",
    "अठ्ठाइस",
    "उनन्तीस",
    "तीस",
    "एकतीस",
    "बत्तीस",
    "तेत्तीस",
    "चौंतीस",
    "पैंतीस",
    "छत्तीस",
    "सैंतीस",
    "अठ्तीस",
    "उनन्चालीस",
    "चालीस",
    "एकचालीस",
    "बयालीस",
    "त्रिचालीस",
    "चवालीस",
    "पैंतालीस",
    "छयालीस",
    "सतचालीस",
    "अठचालीस",
    "उनन्चास",
    "पचास",
    "एकाउन्न",
    "बाउन्न",
    "त्रिपन्न",
    "चवन्न",
    "पचपन्न",
    "छपन्न",
    "सन्ताउन्न",
    "अन्ठाउन्न",
    "उनन्साठी",
    "साठी",
    "एकसाठी",
    "बयसाठी",
    "त्रिसाठी",
    "चौंसठी",
    "पैंसठी",
    "छयसठी",
    "सतसठी",
    "अठसठी",
    "उनन्सत्तरी",
    "सत्तरी",
    "एकहत्तर",
    "बहत्तर",
    "त्रिहत्तर",
    "चौहत्तर",
    "पचहत्तर",
    "छहत्तर",
    "सतहत्तर",
    "अठहत्तर",
    "उनासी",
    "असी",
    "एकासी",
    "बयासी",
    "त्रियासी",
    "चौरासी",
    "पचासी",
    "छयासी",
    "सतासी",
    "अठासी",
    "उनान्नब्बे",
    "नब्बे",
    "एकान्नब्बे",
    "बयान्नब्बे",
    "त्रियान्नब्बे",
    "चौरान्नब्बे",
    "पंचान्नब्बे",
    "छयान्नब्बे",
    "सन्तान्नब्बे",
    "अन्ठान्नब्बे",
    "उनान्सय",
]


def _convert_two_digits(num):
    """Convert a number from 0-99 to Nepali words using the lookup table."""
    return NUM_WORDS_0_99[num]


def _convert_three_digits(num):
    """Convert a number from 0-999 to Nepali words."""
    if num == 0:
        return ""
    parts = []
    hundreds, remainder = divmod(num, 100)
    if hundreds > 0:
        parts.append(ONES[hundreds] + " सय")
    if remainder > 0:
        parts.append(_convert_two_digits(remainder))
    return " ".join(parts)


def _number_to_words(amount_int):
    """
    Convert a non-negative integer to Nepali words using the
    crore / lakh / thousand / hundred grouping used in Nepal.
    Supports amounts up to 99,99,99,999 (ninety-nine crore ...).
    """
    if amount_int == 0:
        return "शून्य"

    crore, remainder = divmod(amount_int, 1_00_00_000)
    lakh, remainder = divmod(remainder, 1_00_000)
    thousand, remainder = divmod(remainder, 1_000)
    hundred_part = remainder  # 0-999

    parts = []
    if crore > 0:
        parts.append(_convert_three_digits(crore) + " करोड")
    if lakh > 0:
        parts.append(_convert_three_digits(lakh) + " लाख")
    if thousand > 0:
        parts.append(_convert_three_digits(thousand) + " हजार")
    if hundred_part > 0:
        parts.append(_convert_three_digits(hundred_part))

    return " ".join(parts)


def amount_to_nepali_words(amount, include_paisa=True):
    """
    Convert a monetary amount to Nepali words in standard Nepali
    banking format, e.g.:

        amount_to_nepali_words(125340.75)
        -> "रुपैयाँ एक लाख पच्चीस हजार तीन सय चालीस रुपैयाँ पचहत्तर पैसा मात्र"

        amount_to_nepali_words(0)
        -> "रुपैयाँ शून्य मात्र"

    Args:
        amount: int or float amount (e.g. 125340.75)
        include_paisa: if False, ignores the decimal/paisa portion
                       entirely (useful when a system only tracks
                       whole rupees).
    """
    amount = round(float(amount), 2)
    rupees = int(amount)
    paisa = round((amount - rupees) * 100)

    # Handle rounding edge case: 99.999 -> paisa == 100
    if paisa == 100:
        rupees += 1
        paisa = 0

    rupee_words = _number_to_words(rupees)

    if include_paisa and paisa > 0:
        paisa_words = _convert_two_digits(paisa)
        return f"रुपैयाँ {rupee_words} रुपैयाँ {paisa_words} पैसा मात्र"

    return f"{rupee_words} मात्र"


if __name__ == "__main__":
    test_amounts = [0, 5, 99, 350, 1000, 15000.50, 125340.75, 999999, 1000000, 12345678.25]
    for amt in test_amounts:
        print(f"{amt:>15} -> {amount_to_nepali_words(amt)}")


class Receipt(AbstractBaseModel):
    class ReferenceType(models.TextChoices):
        SALE = "sale", _("Sale")
        FEE_COLLECTION = "fee_collection", _("Fee Collection")
        VISITOR_ENTRY = "visitor_entry", _("Visitor Entry")

    receipt_no = models.CharField(max_length=16, primary_key=True)
    reference_type = models.CharField(max_length=20, choices=ReferenceType.choices)
    reference_id = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    issued_date = models.DateField()
    issued_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_receipts",
    )
    pdf_file = models.FileField(upload_to="receipts/%Y/%m/", blank=True)

    class Meta:
        ordering = ["-issued_date", "-receipt_no"]
        verbose_name = "Receipt"
        verbose_name_plural = "Receipts"

    def __str__(self) -> str:
        return self.receipt_no

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            self.receipt_no = ReceiptSequence.next_receipt_no()
        super().save(*args, **kwargs)

    @property
    def customer_name(self):
        """Get customer name based on reference type."""
        if self.reference_type == self.ReferenceType.FEE_COLLECTION:
            try:
                fee_collection = FeeCollection.objects.get(id=self.reference_id)
                return fee_collection.member.household_head_name if fee_collection.member else ""
            except FeeCollection.DoesNotExist:
                return ""
        elif self.reference_type == self.ReferenceType.VISITOR_ENTRY:
            try:
                from apps.visitors.models import VisitorEntry

                visitor = VisitorEntry.objects.get(id=self.reference_id)
                return visitor.visitor_name or ""
            except Exception:
                return ""
        return ""

    @property
    def registration_no(self):
        """Get organization registration number."""
        # You can hardcode this or fetch from settings
        return "२६४"  # Shivganga CFG registration number

    @property
    def amount_in_words(self):
        """Convert amount to Nepali words."""
        return amount_to_nepali_words(self.amount)


class FeeCollection(AbstractBaseModel):
    class FeeType(models.TextChoices):
        MEMBERSHIP = "membership", _("Membership")
        RENEWAL = "renewal", _("Renewal")
        ROYALTY = "royalty", _("Royalty")
        VISITOR_ENTRY = "visitor_entry", _("Visitor Entry")
        OTHER = "other", _("Other")
        PENALTY = "penalty", _("Penalty")
        WORM_COMPOST = "worm_compost", _("Worm Compost")
        ARREARS_COLLECTION = "arrears_collection", _("Arrears Collection")
        WILDGRASS = "wildgrass", _("Wildgrass")
        BID_DOCUMENT = "bid_document", _("Bid Document")
        HALL_RENT = "hall_rent", _("Hall Rent")
        CANED_BAMBOO = "caned_bamboo", _("Caned Bamboo")
        FOREST_PRODUCTS = "forest_products", _("Forest Products")
        DEPOSIT_AMOUNT = "deposit", _("Deposit")

    class PaymentStatus(models.TextChoices):
        PAID = "paid", _("Paid")
        DUE = "due", _("Due")
        PARTIAL = "partial", _("Partial")

    member = models.ForeignKey(
        "members.Household",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fee_collections",
    )
    fee_type = models.CharField(max_length=24, choices=FeeType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantity = models.PositiveIntegerField(default=1)
    payment_status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.DUE)
    receipt_no = models.OneToOneField(
        Receipt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fee_collection",
    )
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    description = models.TextField(blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Fee Collection"
        verbose_name_plural = "Fee Collections"

    def __str__(self) -> str:
        return f"{self.fee_type} - {self.amount} - {self.get_payment_status_display()}"

    def get_actual_payment_status(self):
        """Calculate payment status based on amount paid."""
        if self.amount_paid >= self.amount:
            return self.PaymentStatus.PAID
        elif self.amount_paid > 0:
            return self.PaymentStatus.PARTIAL
        return self.PaymentStatus.DUE

    def save(self, *args, **kwargs):
        # Update payment_status based on amount_paid
        self.payment_status = self.get_actual_payment_status()
        super().save(*args, **kwargs)
