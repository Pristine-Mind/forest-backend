import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.forest.models import ForestBlock, Species


class Command(BaseCommand):
    help = "Import species from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/species.json",
            help="Path to the JSON file to import (default: data/species.json)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing species before importing",
        )

    def handle(self, *args, **options):
        file_path = options["file"]

        if not Path(file_path).exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        if options["clear"]:
            count = Species.objects.count()
            Species.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing species"))

        with open(file_path, "r", encoding="utf-8") as f:
            species_data = json.load(f)

        created_count = 0
        updated_count = 0
        error_count = 0

        for species_item in species_data:
            try:
                species_name = species_item.get("species_name")

                species_dict = {
                    "species_name": species_name,
                    "local_name": species_item.get("local_name", ""),
                    "scientific_name": species_item.get("scientific_name", ""),
                }

                species, created = Species.objects.update_or_create(species_name=species_name, defaults=species_dict)

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ Created species {species_name}"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"⟳ Updated species {species_name}"))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"✗ Error importing species {species_name}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed!\n" f"Created: {created_count}\n" f"Updated: {updated_count}\n" f"Errors: {error_count}"
            )
        )
