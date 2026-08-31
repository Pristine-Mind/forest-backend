import csv
from django.core.management.base import BaseCommand
from apps.members.models import Household


class Command(BaseCommand):
    help = "Export household data with household head name, ID, and associated member names"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="households_export.csv",
            help="Output file path for the CSV export (default: households_export.csv)",
        )

    def handle(self, *args, **options):
        output_file = options["output"]

        try:
            households = Household.objects.prefetch_related("members").all()

            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["Household ID", "Household Head Name", "Member Names"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                for household in households:
                    member_names = ", ".join(
                        [member.full_name for member in household.members.all()]
                    )
                    writer.writerow(
                        {
                            "Household ID": household.id,
                            "Household Head Name": household.household_head_name,
                            "Member Names": member_names,
                        }
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Successfully exported {households.count()} households to {output_file}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error exporting households: {str(e)}"))
