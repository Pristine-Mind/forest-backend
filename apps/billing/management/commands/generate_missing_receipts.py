"""
Management command to generate missing receipts for fee collections.

Usage:
    python manage.py generate_missing_receipts
    python manage.py generate_missing_receipts --fee-type membership
    python manage.py generate_missing_receipts --member-id 5
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.billing.models import FeeCollection, Receipt
from apps.billing.tasks import generate_receipt_pdf_task
from apps.core.models import User


class Command(BaseCommand):
    help = "Generate missing receipts for fee collections that have been paid but no receipt exists"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fee-type",
            type=str,
            help="Filter by fee type (e.g., membership, renewal)",
        )
        parser.add_argument(
            "--member-id",
            type=int,
            help="Filter by member/household ID",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually creating receipts",
        )

    def handle(self, *args, **options):
        # Build query
        queryset = FeeCollection.objects.filter(
            amount_paid__gt=0,  # Has payment recorded
            receipt_no__isnull=True,  # No receipt yet
        )

        # Apply filters
        if options.get("fee_type"):
            queryset = queryset.filter(fee_type=options["fee_type"])

        if options.get("member_id"):
            queryset = queryset.filter(member_id=options["member_id"])

        total = queryset.count()
        self.stdout.write(f"Found {total} fee collections needing receipts")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No receipts to generate"))
            return

        if options.get("dry_run"):
            self.stdout.write(self.style.WARNING("DRY RUN - No receipts will be created"))
            for fee in queryset[:5]:
                self.stdout.write(
                    f"  - Fee {fee.id}: {fee.get_fee_type_display()} " f"- {fee.amount_paid} (member: {fee.member})"
                )
            if total > 5:
                self.stdout.write(f"  ... and {total - 5} more")
            return

        # Get system user for issuing receipts
        try:
            system_user = User.objects.filter(is_staff=True).first()
            if not system_user:
                raise CommandError("No staff user found to issue receipts")
        except User.DoesNotExist:
            raise CommandError("User model not found")

        # Generate receipts
        created = 0
        errors = 0
        skipped = 0

        for fee_collection in queryset:
            try:
                receipt = Receipt.objects.create(
                    reference_type=Receipt.ReferenceType.FEE_COLLECTION,
                    reference_id=fee_collection.id,
                    amount=fee_collection.amount_paid,
                    issued_date=date.today(),
                    issued_by=system_user,
                )
                fee_collection.receipt_no = receipt
                fee_collection.save(update_fields=["receipt_no"])

                # Trigger PDF generation
                generate_receipt_pdf_task.delay(receipt.receipt_no)

                created += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Receipt {receipt.receipt_no} created for Fee {fee_collection.id}"))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"✗ Error creating receipt for Fee {fee_collection.id}: {str(e)}"))

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"Created: {created}"))
        self.stdout.write(self.style.WARNING(f"Errors: {errors}"))
        self.stdout.write(f"Total processed: {created + errors}")
