import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.forest.models import ForestBlock, OperationalPlan, Species, TreeCountRegister


class Command(BaseCommand):
    help = "Import tree count records from JSON file (data/treecount.json by default)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/treecount.json",
            help="Path to the JSON file to import (default: data/treecount.json)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing tree count records before importing",
        )

    def handle(self, *args, **options):
        file_path = options["file"]

        # Check if file exists
        if not Path(file_path).exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Clear existing records if requested
        if options["clear"]:
            record_count = TreeCountRegister.objects.count()
            TreeCountRegister.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {record_count} existing tree count records"))

        # Read JSON data
        with open(file_path, "r", encoding="utf-8") as f:
            tree_data_list = json.load(f)

        created_count = 0
        updated_count = 0
        error_count = 0
        skipped_count = 0

        self.stdout.write(f"\nImporting {len(tree_data_list)} tree records from {file_path}...")
        self.stdout.write("=" * 60)

        for idx, tree_data in enumerate(tree_data_list, 1):
            try:
                # Get foreign key references
                block_id = tree_data.get("block")
                species_id = tree_data.get("species")
                plot_number = tree_data.get("plot_number")
                tree_number = tree_data.get("tree_number")

                # Validate required fields
                if not block_id or not plot_number or not tree_number:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⊘ Skipped record {idx}: Missing required fields "
                            f"(block={block_id}, plot={plot_number}, tree={tree_number})"
                        )
                    )
                    skipped_count += 1
                    continue

                # Get or validate foreign key objects exist
                try:
                    block = ForestBlock.objects.get(pk=block_id)
                except ForestBlock.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"⊘ Skipped record {idx}: ForestBlock with id={block_id} not found")
                    )
                    skipped_count += 1
                    continue

                # Get species if specified
                species = None
                if species_id:
                    try:
                        species = Species.objects.get(pk=species_id)
                    except Species.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f"⚠ Record {idx}: Species with id={species_id} not found, skipping")
                        )
                        skipped_count += 1
                        continue

                # Prepare tree count data with proper Decimal conversion
                tree_dict = {
                    "block": block,
                    "species": species,
                    "plot_number": plot_number,
                    "tree_number": tree_number,
                    "girth_cm": self._to_decimal(tree_data.get("girth_cm")),
                    "height_m": self._to_decimal(tree_data.get("height_m")),
                    "tree_class": tree_data.get("tree_class"),
                    "basal_area_sqm": self._to_decimal(tree_data.get("basal_area_sqm")),
                    "stem_volume_cubic_m": self._to_decimal(tree_data.get("stem_volume_cubic_m")),
                    "r_factor": self._to_decimal(tree_data.get("r_factor")),
                    "branch_volume_cubic_m": self._to_decimal(tree_data.get("branch_volume_cubic_m")),
                    "total_volume_cubic_m": self._to_decimal(tree_data.get("total_volume_cubic_m")),
                    "r_less_than_10": self._to_decimal(tree_data.get("r_less_than_10")),
                    "volume_less_than_10_cubic_m": self._to_decimal(tree_data.get("volume_less_than_10_cubic_m")),
                    "gross_volume_cubic_m": self._to_decimal(tree_data.get("gross_volume_cubic_m")),
                    "net_volume_cubic_m": self._to_decimal(tree_data.get("net_volume_cubic_m")),
                    "fuelwood_volume_cubic_m": self._to_decimal(tree_data.get("fuelwood_volume_cubic_m")),
                    "is_harvestable": tree_data.get("is_harvestable", True),
                    "is_active": tree_data.get("is_active", True),
                    "notes": tree_data.get("notes", ""),
                }

                # Create or update tree count record
                record, created = TreeCountRegister.objects.update_or_create(
                    block=block, plot_number=plot_number, tree_number=tree_number, defaults=tree_dict
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Created record {idx}: Block {block.block_name}, " f"Plot {plot_number}, Tree {tree_number}"
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"⟳ Updated record {idx}: Block {block.block_name}, " f"Plot {plot_number}, Tree {tree_number}"
                        )
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error in record {idx} (Block: {tree_data.get('block')}, "
                        f"Plot: {tree_data.get('plot_number')}, Tree: {tree_data.get('tree_number')}): {str(e)}"
                    )
                )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Import Summary:"))
        self.stdout.write(f"  ✓ Created:  {created_count}")
        self.stdout.write(f"  ⟳ Updated:  {updated_count}")
        self.stdout.write(f"  ⊘ Skipped:  {skipped_count}")
        self.stdout.write(f"  ✗ Errors:   {error_count}")
        self.stdout.write(f"  Total:      {len(tree_data_list)}")
        self.stdout.write("=" * 60 + "\n")

    def _to_decimal(self, value):
        """Convert value to Decimal, handling None and various types"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
