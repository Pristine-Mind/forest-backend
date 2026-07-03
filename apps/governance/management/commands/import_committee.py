import json
from datetime import datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.governance.models import CommitteeMember
from apps.members.models import Household, Member


class Command(BaseCommand):
    help = "Import committee members from JSON file (data/committie.json by default)"

    # Mapping of Nepali positions to English position choices
    POSITION_MAPPING = {
        "अध्यक्ष": CommitteeMember.Position.CHAIR,
        "उपाध्यक्ष": CommitteeMember.Position.VICE_CHAIR,
        "सचिव": CommitteeMember.Position.SECRETARY,
        "सह-सचिव": CommitteeMember.Position.JOINT_SECRETARY,
        "कोषाध्यक्ष": CommitteeMember.Position.TREASURER,
        "सदस्य": CommitteeMember.Position.MEMBER,
    }

    # Mapping of Nepali gender to English
    GENDER_MAPPING = {
        "महिला": "Female",
        "पुरुष": "Male",
        "अन्य": "Other",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/committie.json",
            help="Path to the JSON file to import (default: data/committie.json)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing committee members before importing",
        )
        parser.add_argument(
            "--term-years",
            type=int,
            default=5,
            help="Term length in years (default: 5)",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        term_years = options["term_years"]

        # Check if file exists
        if not Path(file_path).exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Clear existing records if requested
        if options["clear"]:
            record_count = CommitteeMember.objects.count()
            CommitteeMember.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {record_count} existing committee members"))

        # Get or create a default household for committee members
        default_household, _ = Household.objects.get_or_create(
            household_head_name="Community Forest Committee",
            defaults={
                "tole": "Committee",
                "wealth_class": "medium",
                "registration_date": datetime.now().date(),
                "status": "active",
            },
        )

        # Read JSON data
        with open(file_path, "r", encoding="utf-8") as f:
            committee_data_list = json.load(f)

        created_count = 0
        updated_count = 0
        error_count = 0
        skipped_count = 0

        # Set term dates
        today = datetime.now().date()
        term_start = today
        term_end = today + timedelta(days=365 * term_years)

        self.stdout.write(f"\nImporting {len(committee_data_list)} committee members from {file_path}...")
        self.stdout.write("=" * 70)
        self.stdout.write(f"Term: {term_start} to {term_end} ({term_years} years)")
        self.stdout.write("=" * 70)

        for idx, member_data in enumerate(committee_data_list, 1):
            try:
                full_name = member_data.get("name", "").strip()
                position_nepali = member_data.get("position", "").strip()
                gender_nepali = member_data.get("gender", "").strip()
                address = member_data.get("address", "").strip()

                # Validate required fields
                if not full_name or not position_nepali:
                    self.stdout.write(self.style.WARNING(f"⊘ Skipped record {idx}: Missing name or position"))
                    skipped_count += 1
                    continue

                # Map Nepali position to English
                position = self.POSITION_MAPPING.get(position_nepali)
                if not position:
                    self.stdout.write(
                        self.style.WARNING(f"⊘ Skipped record {idx} ({full_name}): Unknown position '{position_nepali}'")
                    )
                    skipped_count += 1
                    continue

                # Map Nepali gender to English
                gender = self.GENDER_MAPPING.get(gender_nepali, "Other")

                # Create or get member
                # Try to find existing member by name first
                member = Member.objects.filter(full_name=full_name).first()

                if not member:
                    # Generate a simple citizenship_no based on name and index
                    citizenship_no = f"COMM-{idx:04d}"

                    # Create new member
                    member = Member.objects.create(
                        household=default_household,
                        full_name=full_name,
                        citizenship_no=citizenship_no,
                        membership_type=Member.MembershipType.SPECIAL,
                        membership_status=Member.MembershipStatus.ACTIVE,
                        date_joined=today,
                    )
                    self.stdout.write(self.style.SUCCESS(f"  → Created member: {full_name} ({gender})"))

                # Create or update committee member
                committee_member, created = CommitteeMember.objects.update_or_create(
                    member=member,
                    position=position,
                    term_start=term_start,
                    defaults={
                        "term_end": term_end,
                        "gender": gender,
                        "status": CommitteeMember.Status.ACTIVE,
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ Record {idx}: Created {full_name} as {position_nepali}"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"⟳ Record {idx}: Updated {full_name} as {position_nepali}"))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"✗ Record {idx}: Error importing '{member_data.get('name')}': {str(e)}"))

        # Summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("Import Summary:"))
        self.stdout.write(f"  ✓ Created:  {created_count}")
        self.stdout.write(f"  ⟳ Updated:  {updated_count}")
        self.stdout.write(f"  ⊘ Skipped:  {skipped_count}")
        self.stdout.write(f"  ✗ Errors:   {error_count}")
        self.stdout.write(f"  Total:      {len(committee_data_list)}")
        self.stdout.write("=" * 70 + "\n")
