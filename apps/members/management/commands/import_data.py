import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.members.models import Household, Member

NEPALI_TO_ENGLISH = str.maketrans(
    "०१२३४५६७८९",
    "0123456789",
)


class Command(BaseCommand):
    help = "Import households and members from JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to JSON file",
        )

        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing records",
        )

    def handle(self, *args, **options):

        file_path = Path(options["json_file"])

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"{file_path} does not exist."))
            return

        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        created_households = 0
        updated_households = 0
        created_members = 0
        updated_members = 0
        skipped = 0

        with transaction.atomic():

            for index, record in enumerate(records, start=1):

                try:

                    head_name = self.clean(record.get("head_of_household"))

                    if not head_name:
                        skipped += 1
                        continue

                    defaults = {
                        "tole": self.clean(record.get("tole")),
                        "wealth_class": Household.WealthClass.MEDIUM,
                        "population_male": 0,
                        "population_female": 0,
                        "livestock_cattle": 0,
                        "livestock_buffalo": 0,
                        "livestock_goat": 0,
                        "education_level": Household.EducationLevel.BASIC,
                        "occupation": "",
                        "caste_ethnicity": "",
                        "registration_date": date.today(),
                        "date_joined": date.today(),
                        "entry_fee_type": Household.EntryFeeType.NEW_HOUSEHOLD,
                        "membership_type": Household.MembershipType.GENERAL,
                        "membership_status": Household.MembershipStatus.ACTIVE,
                        "status": Household.Status.ACTIVE,
                        "citizenship_no": self.clean(record.get("citizenship_no")),
                        "contact_number": self.clean(record.get("contact_number")),
                        "membership_number": self.clean(record.get("member_no")),
                    }

                    household, created = Household.objects.get_or_create(
                        household_head_name=head_name,
                        defaults=defaults,
                    )

                    if created:
                        created_households += 1

                    elif options["update"]:

                        for field, value in defaults.items():
                            setattr(household, field, value)

                        household.save()

                        updated_households += 1

                    member_name = self.clean(record.get("related_member"))

                    relation = self.clean(record.get("relation"))

                    if member_name:

                        member, member_created = Member.objects.get_or_create(
                            household=household,
                            full_name=member_name,
                            defaults={
                                "relation": relation,
                            },
                        )

                        if member_created:

                            created_members += 1

                        elif options["update"]:

                            member.relation = relation
                            member.save(update_fields=["relation"])

                            updated_members += 1

                except Exception as ex:

                    skipped += 1

                    self.stderr.write(self.style.ERROR(f"Row {index}: {ex}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Import Completed"))
        self.stdout.write("-" * 50)
        self.stdout.write(f"Households Created : {created_households}")
        self.stdout.write(f"Households Updated : {updated_households}")
        self.stdout.write(f"Members Created    : {created_members}")
        self.stdout.write(f"Members Updated    : {updated_members}")
        self.stdout.write(f"Skipped            : {skipped}")

    @staticmethod
    def clean(value):

        if value is None:
            return ""

        value = str(value).strip()

        if value.lower() in {
            "",
            "none",
            "null",
            "nan",
            "-",
            "--",
        }:
            return ""

        return value.translate(NEPALI_TO_ENGLISH)
