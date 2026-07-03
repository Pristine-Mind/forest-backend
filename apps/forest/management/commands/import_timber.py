import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.forest.models import ForestBlock, TimberCollection


class Command(BaseCommand):
    help = "Import forest blocks from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/timber.json",
            help="Path to the JSON file to import (default: data/timber.json)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing timber records before importing",
        )

    def handle(self, *args, **options):
        file_path = options["file"]

        # Check if file exists
        if not Path(file_path).exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Clear existing timber records if requested
        if options["clear"]:
            count = TimberCollection.objects.count()
            TimberCollection.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing timber records"))

        # Read and import JSON data
        with open(file_path, "r", encoding="utf-8") as f:
            timber_data = json.load(f)

        created_count = 0
        updated_count = 0
        error_count = 0

        for timber_entry in timber_data:
            try:
                # Prepare data
                block_dict = {
                    "block_id": timber_entry.get("block_id"),
                    "species_id": timber_entry.get("species_id"),
                    "wood_volume": Decimal(str(timber_entry.get("wood_volume", 0))),
                    "firewood": Decimal(str(timber_entry.get("firewood", 0))),
                }

                # Create or update block
                block, created = TimberCollection.objects.get_or_create(**block_dict)

            except Exception as e:
                print(f"Error importing timber entry: {timber_entry}. Error: {e}")
                error_count += 1
                self.stdout.write(self.style.ERROR(f"✗ Error importing data"))

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed!\n" f"Created: {created_count}\n" f"Updated: {updated_count}\n" f"Errors: {error_count}"
            )
        )
