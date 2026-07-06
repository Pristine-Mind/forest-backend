from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.forest.models import ForestBoundary


class Command(BaseCommand):
    help = "Import forest boundary polygons from a GeoJSON FeatureCollection file"

    def add_arguments(self, parser):
        parser.add_argument("geojson_path", type=str)
        parser.add_argument("--clear", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["geojson_path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        with path.open() as f:
            collection = json.load(f)

        if options["clear"]:
            deleted, _ = ForestBoundary.objects.all().delete()
            self.stdout.write(f"Deleted {deleted} existing boundaries.")

        created = 0
        for feature in collection.get("features", []):
            name = feature.get("properties", {}).get("name", "Unnamed")
            geometry = feature["geometry"]

            if geometry["type"] != "Polygon":
                self.stdout.write(self.style.WARNING(f"  Skipped non-polygon: {name}"))
                continue

            # GeoJSON Polygon coordinates[0] is the outer ring
            coordinates = geometry["coordinates"][0]

            obj = ForestBoundary(
                name=name,
                coordinates=coordinates,
                source_notes=f"Imported from GeoJSON. {len(coordinates)} points.",
            )
            obj.save()
            self.stdout.write(f"  ✓ {name} ({len(coordinates)} points)")
            created += 1

        self.stdout.write(self.style.SUCCESS(f"\nImported {created} boundaries."))
