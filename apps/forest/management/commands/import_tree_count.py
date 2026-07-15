import csv
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.forest.models import ForestBlock, OperationalPlan, Species, TreeCountRegister


class DryRunRollback(Exception):
    """Raised internally to unwind the transaction after a --dry-run pass."""


class Command(BaseCommand):
    help = "Import tree count register rows from a CSV file into TreeCountRegister."

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the tree_register.csv file")
        parser.add_argument(
            "--operational-plan-id",
            type=int,
            required=False,
            default=None,
            help="Optional ID of the OperationalPlan these trees belong to (left NULL if omitted)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and print what would happen without committing to the database",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_file"]
        op_plan_id = options["operational_plan_id"]
        dry_run = options["dry_run"]

        try:
            rows = self._load_rows(csv_path)
        except FileNotFoundError as exc:
            raise CommandError(f"CSV file not found: {csv_path}") from exc

        species_cache = {}
        imported = 0
        skipped = []

        try:
            with transaction.atomic():
                for i, row in enumerate(rows, start=1):
                    block_key = row["block_no"].strip()
                    try:
                        block = ForestBlock.objects.get(block_no=block_key)
                    except ForestBlock.DoesNotExist:
                        skipped.append((i, row, f"no ForestBlock matches block_no={block_key!r}"))
                        continue
                    except ForestBlock.MultipleObjectsReturned:
                        skipped.append((i, row, f"multiple ForestBlock rows match block_no={block_key!r}"))
                        continue

                    species_id_raw = (row.get("species_id") or "").strip()
                    if not species_id_raw:
                        skipped.append((i, row, f"species {row['species_name']!r} has no species_id in CSV (e.g. अन्य)"))
                        continue

                    try:
                        species = self._resolve_species(int(species_id_raw), species_cache)
                    except Species.DoesNotExist:
                        skipped.append((i, row, f"no Species row with id={species_id_raw}"))
                        continue

                    record = TreeCountRegister(
                        block=block,
                        operational_plan_id=op_plan_id,
                        species=species,
                        plot_number=self._to_int(row["plot_number"]),
                        tree_number=self._to_int(row["row_no"]),
                        girth_cm=self._to_decimal(row["girth_cm"]),
                        height_m=self._to_decimal(row["height_m"]),
                        tree_class=row["tree_class"].strip() or None,
                        basal_area_sqm=self._to_decimal(row["basal_area_sqm"]),
                        stem_volume_cubic_m=self._to_decimal(row["stem_volume_cubic_m"]),
                        r_factor=self._to_decimal(row["r_factor"]) or Decimal("0.00"),
                        branch_volume_cubic_m=self._to_decimal(row["branch_volume_cubic_m"]),
                        total_volume_cubic_m=self._to_decimal(row["total_volume_cubic_m"]),
                        r_less_than_10=self._to_decimal(row["r_less_than_10"]) or Decimal("0.00"),
                        volume_less_than_10_cubic_m=self._to_decimal(row["volume_less_than_10_cubic_m"]),
                        gross_volume_cubic_m=self._to_decimal(row["gross_volume_cubic_m"]),
                        net_volume_cubic_m=self._to_decimal(row["net_volume_cubic_m"]),
                        fuelwood_volume_cubic_m=self._to_decimal(row["fuelwood_volume_cubic_m"]),
                    )
                    record.save()
                    imported += 1

                    if dry_run:
                        self.stdout.write(
                            f"[dry-run] row {i} - {species.species_name} "
                            f"(block {block_key}, plot {record.plot_number}): "
                            f"girth={record.girth_cm} height={record.height_m} "
                            f"net_vol={record.net_volume_cubic_m} fuelwood={record.fuelwood_volume_cubic_m}"
                        )

                if dry_run:
                    raise DryRunRollback()
        except DryRunRollback:
            pass

        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"[dry-run] Would import {imported} row(s); nothing was committed."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Imported {imported} row(s) into TreeCountRegister."))

        if skipped:
            self.stdout.write(self.style.ERROR(f"\n{len(skipped)} row(s) skipped:"))
            for i, row, reason in skipped:
                self.stdout.write(
                    self.style.ERROR(
                        f"  row {i} (block={row.get('block_no')}, plot={row.get('plot_number')}, "
                        f"species={row.get('species_name')}): {reason}"
                    )
                )

    # -- helpers ----------------------------------------------------------

    def _load_rows(self, csv_path):
        with open(csv_path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _resolve_species(self, species_id, cache):
        if species_id in cache:
            return cache[species_id]
        species = Species.objects.get(pk=species_id)  # raises Species.DoesNotExist if missing
        cache[species_id] = species
        return species

    @staticmethod
    def _to_decimal(value):
        value = (value or "").strip()
        if value == "":
            return None
        try:
            return Decimal(value)
        except InvalidOperation:
            return None

    @staticmethod
    def _to_int(value):
        value = (value or "").strip()
        if value == "":
            return None
        try:
            return int(float(value))
        except ValueError:
            return None
