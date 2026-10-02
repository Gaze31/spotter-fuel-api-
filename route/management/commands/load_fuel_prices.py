"""
One-time data load: CSV -> Station rows -> geocode unique (city, state)
pairs -> backfill lat/lon.

Run once, before you ever hit the live API:
    python manage.py load_fuel_prices data/fuel-prices-for-be-assessment.csv
"""
import csv
import time

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from route.models import Station
from route.services.geocoding import geocode_city_state


class Command(BaseCommand):
    help = "Load the fuel prices CSV and geocode unique city/state pairs."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        # Step 1: load every row as a Station, no coordinates yet.
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            stations = [
                Station(
                    truckstop_id=int(row["OPIS Truckstop ID"]),
                    name=row["Truckstop Name"],
                    address=row["Address"],
                    city=row["City"],
                    state=row["State"],
                    rack_id=int(row["Rack ID"]),
                    retail_price=row["Retail Price"],
                )
                for row in reader
            ]
            Station.objects.bulk_create(stations, ignore_conflicts=True)
        self.stdout.write(f"Loaded {len(stations)} stations (coordinates pending).")

        # Step 2: geocode unique (city, state) pairs and backfill.
        unique_locations = Station.objects.values_list("city", "state").distinct()
        total = len(unique_locations)
        self.stdout.write(f"Starting geocoding for {total} unique locations...")

        geocoded_map = {}
        for i, (city, state) in enumerate(unique_locations, start=1):
            if not city or not state:
                continue

            result = geocode_city_state(city, state)
            if result is None:
                self.stdout.write(f"  no match: {city}, {state}")
            else:
                geocoded_map[(city, state)] = result

            if i % 200 == 0:
                self.stdout.write(f"  ...{i}/{total} done")

            time.sleep(1.0)

        # Step 3: apply results to matching Station rows, in batches.
        self.stdout.write("Updating Station rows in the database...")
        updated_stations = []
        for station in Station.objects.all():
            key = (station.city, station.state)
            if key in geocoded_map:
                station.latitude, station.longitude = geocoded_map[key]
                updated_stations.append(station)

        if updated_stations:
            with transaction.atomic():
                Station.objects.bulk_update(
                    updated_stations, ["latitude", "longitude"], batch_size=500
                )
            self.stdout.write(self.style.SUCCESS(
                f"Updated {len(updated_stations)} station records."
            ))
        else:
            self.stdout.write(self.style.WARNING("No records were updated."))