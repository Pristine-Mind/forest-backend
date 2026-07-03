import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.forest.models import ForestBlock


class Command(BaseCommand):
    help = "Import forest blocks from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/block.json",
            help="Path to the JSON file to import (default: data/block.json)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing blocks before importing",
        )

    def handle(self, *args, **options):
        file_path = options["file"]

        # Check if file exists
        if not Path(file_path).exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Clear existing blocks if requested
        if options["clear"]:
            count = ForestBlock.objects.count()
            ForestBlock.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing blocks"))

        # Read and import JSON data
        with open(file_path, "r", encoding="utf-8") as f:
            blocks_data = json.load(f)

        created_count = 0
        updated_count = 0
        error_count = 0

        for block_data in blocks_data:
            try:
                block_no = block_data.get("block_no")

                # Prepare data
                block_dict = {
                    "block_no": block_no,
                    "block_name": block_data.get("block_no", ""),  # Use block_no as name if not provided
                    "title": block_data.get("title", ""),
                    "total_area_ha": Decimal(str(block_data.get("total_area_ha", 0))),
                    "productive_area_ha": (
                        Decimal(str(block_data.get("productive_area_ha", 0)))
                        if block_data.get("productive_area_ha")
                        else None
                    ),
                    "canopy_percent": (
                        Decimal(str(block_data.get("canopy_percent", 0))) if block_data.get("canopy_percent") else None
                    ),
                    "soil_types": block_data.get("soil", []),
                    "forest_type": block_data.get("forest_type", ""),
                    "forest_condition": block_data.get("forest_condition", ""),
                    "major_species": block_data.get("major_species", []),
                    "forest_management_activities": block_data.get("forest_management_activities", []),
                    "non_timber_forest_products": block_data.get("non_timber_forest_products", []),
                    "wildlife_species": block_data.get("wildlife", []),
                    "boundaries": block_data.get("boundaries", {}),
                }

                # Create or update block
                block, created = ForestBlock.objects.update_or_create(block_no=block_no, defaults=block_dict)

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ Created block {block_no}: {block.title}"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"⟳ Updated block {block_no}: {block.title}"))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"✗ Error importing block {block_data.get('block_no')}: {str(e)}"))

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed!\n" f"Created: {created_count}\n" f"Updated: {updated_count}\n" f"Errors: {error_count}"
            )
        )
