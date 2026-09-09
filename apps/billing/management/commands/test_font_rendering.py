"""
Test command to verify font registration and PDF rendering.

Usage:
    python manage.py test_font_rendering
    python manage.py test_font_rendering --receipt-no REC-0001
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class Command(BaseCommand):
    help = "Test Devanagari font registration and PDF rendering"

    def add_arguments(self, parser):
        parser.add_argument(
            "--receipt-no",
            type=str,
            help="Receipt number to regenerate PDF for",
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Font Registration Test"))
        self.stdout.write("=" * 60)

        # Test font paths
        self.stdout.write("\n1. Testing font file paths...")

        possible_paths = [
            os.path.join(settings.BASE_DIR, "static", "fonts"),
            os.path.join(settings.BASE_DIR, "..", "static", "fonts"),
            "/code/static/fonts",
            "/app/static/fonts",
        ]

        fonts_found_path = None
        for path in possible_paths:
            regular_path = os.path.join(path, "NotoSansDevanagari-Regular.ttf")
            bold_path = os.path.join(path, "NotoSansDevanagari-Bold.ttf")

            regular_exists = os.path.exists(regular_path)
            bold_exists = os.path.exists(bold_path)

            status = self.style.SUCCESS("✓") if (regular_exists and bold_exists) else self.style.ERROR("✗")
            self.stdout.write(f"  {status} {path}")
            self.stdout.write(f"      Regular: {regular_exists} ({regular_path})")
            self.stdout.write(f"      Bold: {bold_exists} ({bold_path})")

            if regular_exists and bold_exists:
                fonts_found_path = path

        # Test font registration
        self.stdout.write("\n2. Testing font registration...")

        from apps.billing.pdf import _register_devanagari_fonts

        try:
            font_regular, font_bold = _register_devanagari_fonts()
            self.stdout.write(f"  {self.style.SUCCESS('✓')} Fonts registered as: {font_regular}, {font_bold}")

            registered = pdfmetrics.getRegisteredFontNames()
            self.stdout.write(f"  Registered fonts count: {len(registered)}")

            if "NotoSansDevanagari" in registered:
                self.stdout.write(self.style.SUCCESS("  ✓ NotoSansDevanagari is registered"))
            else:
                self.stdout.write(self.style.WARNING("  ! NotoSansDevanagari not in registry"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error registering fonts: {e}"))
            import traceback

            traceback.print_exc()

        # Test PDF generation
        self.stdout.write("\n3. Testing PDF generation...")

        receipt_no = options.get("receipt_no")

        if receipt_no:
            try:
                from apps.billing.models import Receipt
                from apps.billing.pdf import generate_receipt_pdf

                receipt = Receipt.objects.get(receipt_no=receipt_no)
                self.stdout.write(f"  Found receipt: {receipt.receipt_no}")

                buffer = generate_receipt_pdf(receipt)
                pdf_size = len(buffer.getvalue())

                self.stdout.write(self.style.SUCCESS(f"  ✓ PDF generated successfully ({pdf_size} bytes)"))
                self.stdout.write(f"  Customer name: {receipt.customer_name}")
                self.stdout.write(f"  Amount: {receipt.amount}")
                self.stdout.write(f"  Amount in words: {receipt.amount_in_words}")

                # Verify Nepali text in PDF
                pdf_content = buffer.getvalue().decode("latin-1", errors="ignore")
                nepali_chars = ["श", "ी", "ग", "ं", "म", "त", "र", "ु", "व", "ज", "द", "स", "न"]
                found_nepali = any(char in pdf_content for char in nepali_chars)

                if found_nepali:
                    self.stdout.write(self.style.SUCCESS("  ✓ Nepali text detected in PDF"))
                else:
                    self.stdout.write(self.style.WARNING("  ! Nepali text not found in PDF (fonts may be falling back)"))

            except Receipt.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"  ✗ Receipt {receipt_no} not found"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error generating PDF: {e}"))
                import traceback

                traceback.print_exc()
        else:
            self.stdout.write("  (Skipped - use --receipt-no to test with actual receipt)")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Test complete!")
