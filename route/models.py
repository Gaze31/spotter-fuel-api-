from django.db import models


class Station(models.Model):
    """
    One row per truckstop from the fuel-prices CSV. Loaded once via the
    load_fuel_prices management command, not touched at request time.
    """

    truckstop_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)  # highway/exit text, not a street address
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=10)
    rack_id = models.IntegerField()
    retail_price = models.DecimalField(max_digits=8, decimal_places=5)

    # Filled in by the geocoding step in load_fuel_prices, keyed off
    # (city, state) since the CSV has no coordinates of its own.
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # TODO: once this is populated and you're querying "stations near this
    # route" on every request, think about whether a plain FloatField scan
    # is fast enough at 8k rows, or whether you want a DB index / a
    # geospatial extension. Worth a sentence in your README either way -
    # "I considered X, didn't need it because Y" reads better than silence.

    class Meta:
        indexes = [
            models.Index(fields=["city", "state"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"
