"""
One-time geocoding of station city/state into lat/lon. Called only from
the load_fuel_prices management command - never from a live request.
"""
import time

import requests


def geocode_city_state(city: str, state: str) -> tuple[float, float] | None:
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": f"{city}, {state}, USA", "format": "json"},
        headers={"User-Agent": "spotter-fuel-api (student project)"},
    )
    data = response.json()

    if not data:
        return None

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return (lat, lon)
