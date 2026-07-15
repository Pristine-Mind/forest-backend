from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.forest.models import ForestBlock, Species, TimberCollection

BLOCK_LOOKUP_FIELD = "block_no"
SPECIES_LOOKUP_FIELD = "species_name"

BLOCK_NAMES = {
    1: "१",
    2: "२",
}

# Data transcribed from the source table.
# wood_volume is in घन फिट, firewood is in चट्टा.
DATA = [
    {"block_id": 1, "species": 2, "wood_volume": "3638.21", "firewood": "10.91"},
    {"block_id": 2, "species": 2, "wood_volume": "697.90", "firewood": "2.09"},
    {"block_id": 1, "species": 3, "wood_volume": "136.57", "firewood": "0.41"},
    {"block_id": 2, "species": 3, "wood_volume": "374.61", "firewood": "1.09"},
    {"block_id": 1, "species": 8, "wood_volume": "388.53", "firewood": "1.17"},
    {"block_id": 2, "species": 8, "wood_volume": "94.08", "firewood": "0.29"},
    {"block_id": 1, "species": 5, "wood_volume": "137.00", "firewood": "0.41"},
    {"block_id": 2, "species": 5, "wood_volume": "0.00", "firewood": "0.00"},
    {"block_id": 1, "species": 4, "wood_volume": "0.00", "firewood": "0.00"},
    {"block_id": 2, "species": 4, "wood_volume": "113.74", "firewood": "0.34"},
]


class Command(BaseCommand):
    help = "Import TimberCollection records (काठ/दाउरा) from the source table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be imported without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for row in DATA:
                block_name = BLOCK_NAMES[row["block_id"]]

                block = ForestBlock.objects.get(**{BLOCK_LOOKUP_FIELD: block_name})

                species = Species.objects.get(id=row["species"])
                print(species.id)

                defaults = {
                    "wood_volume": Decimal(row["wood_volume"]),
                    "firewood": Decimal(row["firewood"]),
                }

                if dry_run:
                    self.stdout.write(f"[dry-run] {block_name} - {row['species']}: {defaults}")
                    continue

                obj, created = TimberCollection.objects.update_or_create(
                    block=block,
                    species=species,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes made."))
                transaction.set_rollback(True)
                return

        self.stdout.write(self.style.SUCCESS(f"Import complete: {created_count} created, {updated_count} updated."))
