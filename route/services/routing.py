"""
The one (or two/three, max) live routing API call per request.
"""
from typing import TypedDict


class RouteResult(TypedDict):
    route_mileages: list[float]
    geometry: list[tuple[float, float]]  # ordered (lat, lon) points along the path
    distance_miles: float


import requests
from route.services.fuel_optimizer import haversine_miles

def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict:
    """
    Fetches a driving route from OSRM, flippes the coordinates to (lat, lon), 
    and calculates cumulative step-by-step track mileages.
    
    Returns a dict adhering to RouteResult typing.
    """
    # 1. Build the OSRM API URL matching the [lon, lat] convention
    url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    
    # 2. Execute request and parse JSON payload
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    # 3. Pull total distance and convert meters to miles
    meters = data["routes"][0]["distance"]
    distance_miles = meters * 0.000621371
    
    # 4. Pull out and flip coordinates from [lon, lat] to (lat, lon)
    geojson_coordinates = data["routes"][0]["geometry"]["coordinates"]
    flipped_points = [(pt[1], pt[0]) for pt in geojson_coordinates]
    
    # 5. Compute sequential running total mileages matching point indices
    route_mileages = [0.0]
    running_total = 0.0
    for i in range(1, len(flipped_points)):
        prev_point = flipped_points[i - 1]
        current_point = flipped_points[i]
        
        # Calculate step distance using our domain service formula
        step_distance = haversine_miles(prev_point[0], prev_point[1], current_point[0], current_point[1])
        running_total += step_distance
        route_mileages.append(running_total)
        
    return {
        "distance_miles": distance_miles,
        "geometry": flipped_points,
        "route_mileages": route_mileages
    }
