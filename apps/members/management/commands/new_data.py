from datetime import date

import openpyxl
from django.core.management.base import BaseCommand

from apps.members.models import Household, Member


class Command(BaseCommand):
    help = "Import households and members from the 5-column sheet."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to the .xlsx file")

    def handle(self, *args, **options):
        wb = openpyxl.load_workbook(options["file"], data_only=True)
        ws = wb.active

        created_households = 0
        created_members = 0

        # skip header row
        for row in ws.iter_rows(min_row=2, values_only=True):
            head_name, head_name_en, member_name, member_name_en, relation = (row + (None,) * 5)[:5]

            if not head_name:
                continue

            household, was_created = Household.objects.get_or_create(
                household_head_name=str(head_name).strip(),
                defaults={
                    "english_name": (str(head_name_en).strip() if head_name_en else None),
                    "wealth_class": Household.WealthClass.MEDIUM,
                    "registration_date": date.today(),
                },
            )
            if was_created:
                created_households += 1

            if member_name:
                _, member_created = Member.objects.get_or_create(
                    household=household,
                    full_name=str(member_name).strip(),
                    defaults={
                        "full_name_en": (str(member_name_en).strip() if member_name_en else None),
                        "relation": (str(relation).strip() if relation else None),
                    },
                )
                if member_created:
                    created_members += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Households created: {created_households}, Members created: {created_members}"
        ))