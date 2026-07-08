from datetime import date
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.members.models import Household, Member

COLUMN_MAP = {
    "उपभोक्ता (Consumer)": "household_head_name",
    "सह उपभोक्ता (Co-consumer)": "co_consumer",
    "नाता (Relation)": "relation",
    "जात/जाति (Caste)": "caste",
    "म (Male)": "male",
    "प (Female)": "female",
    "जम्मा (Total)": "total",
    "गाई/गोरु (Cow/Ox)": "cow",
    "भैंसी/राँगा (Buffalo)": "buffalo",
    "बाख्रा/भेडा (Goat/Sheep)": "goat",
    "निरक्षर (Illiterate)": "illiterate",
    "७ सम्म (Up to 7)": "upto7",
    "७ देखि १० सम्म (7-10)": "upto10",
    "१० भन्दा माथि (Above 10)": "above10",
    "कड्टा (Difficult)": "difficult",
    "पेशा (Occupation)": "occupation",
    "टोल (Tole/Area)": "tole",
}


NEPALI_DIGITS = str.maketrans(
    "०१२३४५६७८९",
    "0123456789",
)


class Command(BaseCommand):
    help = "Import Household Excel"

    def add_arguments(self, parser):

        parser.add_argument("excel", type=str, help="Excel file")

        parser.add_argument("--update", action="store_true", help="Update existing households")

    def handle(self, *args, **options):

        excel = Path(options["excel"])

        if not excel.exists():
            self.stderr.write(self.style.ERROR("Excel not found"))
            return

        df = pd.read_excel(excel)

        df.rename(columns=COLUMN_MAP, inplace=True)

        created = 0
        updated = 0
        members_created = 0
        skipped = 0

        with transaction.atomic():

            for idx, row in df.iterrows():

                try:

                    head_name = self.clean(row.get("household_head_name"))

                    if not head_name:
                        skipped += 1
                        continue

                    male = self.to_int(row.get("male"))
                    female = self.to_int(row.get("female"))
                    total = self.to_int(row.get("total"))

                    if total and (male + female != total):
                        self.stdout.write(
                            self.style.WARNING(f"Row {idx+2}: Population mismatch " f"{male}+{female}!={total}")
                        )

                    defaults = {
                        "tole": self.clean(row.get("tole")),
                        "wealth_class": Household.WealthClass.MEDIUM,
                        "population_male": male,
                        "population_female": female,
                        "livestock_cattle": self.to_int(row.get("cow")),
                        "livestock_buffalo": self.to_int(row.get("buffalo")),
                        "livestock_goat": self.to_int(row.get("goat")),
                        "occupation": self.clean(row.get("occupation")),
                        "caste_ethnicity": self.clean(row.get("caste")),
                        "education_level": self.get_education(row),
                        "registration_date": date.today(),
                        "date_joined": date.today(),
                    }

                    household, is_created = Household.objects.get_or_create(
                        household_head_name=head_name,
                        defaults=defaults,
                    )

                    if is_created:
                        created += 1

                    elif options["update"]:

                        for field, value in defaults.items():
                            setattr(household, field, value)

                        household.save()
                        updated += 1

                    member_name = self.clean(row.get("co_consumer"))
                    relation = self.clean(row.get("relation"))

                    if member_name:

                        _, member_created = Member.objects.get_or_create(
                            household=household, full_name=member_name, defaults={"relation": relation}
                        )

                        if not member_created and options["update"]:
                            member = Member.objects.get(
                                household=household,
                                full_name=member_name,
                            )
                            member.relation = relation
                            member.save(update_fields=["relation"])

                        if member_created:
                            members_created += 1

                except Exception as e:

                    skipped += 1

                    self.stderr.write(self.style.ERROR(f"Row {idx+2}: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"""
Import Finished

Households Created : {created}
Households Updated : {updated}
Members Created    : {members_created}
Skipped            : {skipped}
"""
            )
        )

    @staticmethod
    def clean(value):

        if pd.isna(value):
            return ""

        value = str(value).strip()

        if value.lower() == "nan":
            return ""

        if value in ["-", "—", "None", ""]:
            return ""

        return value

    def to_int(self, value):

        value = self.clean(value)

        if not value:
            return 0

        value = value.translate(NEPALI_DIGITS)

        try:
            return int(float(value))
        except Exception:
            return 0

    def get_education(self, row):

        illiterate = self.to_int(row.get("illiterate"))
        upto7 = self.to_int(row.get("upto7"))
        upto10 = self.to_int(row.get("upto10"))
        above10 = self.to_int(row.get("above10"))

        if illiterate > 0:
            return Household.EducationLevel.ILLITERATE

        if upto7 > 0 or upto10 > 0:
            return Household.EducationLevel.BASIC

        if above10 > 0:
            return Household.EducationLevel.SECONDARY_PLUS

        return Household.EducationLevel.BASIC
