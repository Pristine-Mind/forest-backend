import csv
import os
from django.core.management.base import BaseCommand, CommandError
from apps.members.models import Household, Member


class Command(BaseCommand):
    help = "Update household and member english_name fields from a CSV or XLSX file"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Path to CSV or XLSX file with columns: Household ID, Household Head Name English, Member Names English",
        )

    def _read_xlsx(self, file_path):
        """Read data from XLSX file and return list of dictionaries"""
        try:
            import openpyxl
        except ImportError:
            raise CommandError("openpyxl is required for XLSX support. Install it with: pip install openpyxl")

        try:
            workbook = openpyxl.load_workbook(file_path)
            worksheet = workbook.active
            
            # Get headers from first row
            headers = []
            for cell in worksheet[1]:
                headers.append(cell.value)
            
            # Read data rows
            rows = []
            for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                row_dict = {}
                for col_idx, header in enumerate(headers):
                    if header:
                        row_dict[header] = row[col_idx] if col_idx < len(row) else None
                rows.append((row_idx, row_dict))
            
            return rows
        except Exception as e:
            raise CommandError(f"Error reading XLSX file: {str(e)}")

    def _read_csv(self, file_path):
        """Read data from CSV file and return list of dictionaries"""
        rows = []
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise CommandError("CSV file is empty")
                
                for row_num, row in enumerate(reader, start=2):
                    rows.append((row_num, row))
            
            return rows
        except Exception as e:
            raise CommandError(f"Error reading CSV file: {str(e)}")

    def handle(self, *args, **options):
        file_path = options["file_path"]

        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        # Determine file type
        _, file_ext = os.path.splitext(file_path)
        file_ext = file_ext.lower()

        if file_ext in [".xlsx", ".xls"]:
            rows = self._read_xlsx(file_path)
        elif file_ext == ".csv":
            rows = self._read_csv(file_path)
        else:
            raise CommandError(f"Unsupported file format: {file_ext}. Use CSV or XLSX.")

        household_updated = 0
        members_updated = 0
        skipped_count = 0
        failed_entries = []

        for row_num, row in rows:
            try:
                household_id = row.get("Household ID") or row.get("ID")
                household_english_name = row.get("Household Head Name English") or row.get("English Name")
                members_english_names = row.get("Member Names English") or row.get("Member Names")

                if not household_id:
                    skipped_count += 1
                    continue

                household = Household.objects.get(id=int(household_id))

                # Update household english name
                if household_english_name:
                    household.english_name = str(household_english_name).strip()
                    household.save()
                    household_updated += 1

                # Update member english names
                if members_english_names:
                    member_names = [name.strip() for name in str(members_english_names).split(",")]
                    household_members = list(household.members.all())

                    for idx, member_name in enumerate(member_names):
                        if idx < len(household_members):
                            member = household_members[idx]
                            member.full_name_en = member_name
                            member.save()
                            members_updated += 1

            except Household.DoesNotExist:
                failed_entries.append(f"Row {row_num}: Household ID {household_id} not found")
            except (ValueError, KeyError, AttributeError) as e:
                failed_entries.append(f"Row {row_num}: Invalid data - {str(e)}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Successfully updated {household_updated} households and {members_updated} members"
            )
        )

        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f"⊘ Skipped {skipped_count} rows (missing household ID)")
            )

        if failed_entries:
            self.stdout.write(self.style.ERROR(f"✗ Failed entries:"))
            for entry in failed_entries:
                self.stdout.write(self.style.ERROR(f"  {entry}"))
