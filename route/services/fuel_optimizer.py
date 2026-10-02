"""
The actual problem: given a route and a list of candidate fuel stations,
pick where to stop and compute total cost.

This file is the real assessment. Everything else in this project is
plumbing to get you here.
"""
import math


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, in miles. Filled in -
    this is a known formula, not the part worth your time right now."""
    r = 3958.8  # earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def optimize_fuel_stops(route_points, route_mileages, stations, haversine_miles, max_range=500.0, buffer=20.0):
    """
    Finds the cheapest fuel stops along a route given a vehicle range constraint.
    
    route_points: List of (lat, lon) coordinates representing the route path.
    route_mileages: List of cumulative mileages from the start for each point in route_points.
    stations: List of dicts, each with 'latitude', 'longitude', 'price', and 'name'.
    haversine_miles: Function calculating distance between two (lat, lon) points.
    """
    total_distance = route_mileages[-1]
    current_mileage = 0.0
    chosen_stops = []
    
    # Pre-calculate the closest route mileage for every station to avoid O(N*M) loops inside the main loop
    stations_with_mileage = []
    for station in stations:
        # Find the point on the route closest to this station
        min_dist = float('inf')
        closest_route_mile = 0.0
        
        for pt, mile in zip(route_points, route_mileages):
            d = haversine_miles(station['latitude'], station['longitude'], pt[0], pt[1])
            if d < min_dist:
                min_dist = d
                closest_route_mile = mile
        
        # Threshold choice: 20.0 miles allows capturing major highway-adjacent plazas 
        # without deviating significantly far off-course into unroutable terrain.
        if min_dist <= 20.0:
            station_copy = station.copy()
            station_copy['route_mileage'] = closest_route_mile
            stations_with_mileage.append(station_copy)

    # Main routing loop
    while current_mileage + max_range < total_distance:
        # Define the reachable window with a safety buffer
        max_reachable_mileage = current_mileage + (max_range - buffer)
        
        # Find candidate stations within the reachable window ahead of us
        candidates = [
            s for s in stations_with_mileage 
            if current_mileage < s['route_mileage'] <= max_reachable_mileage
        ]
        
        # Gap 1 Handle: If no stations are reachable within our range, the route fails
        if not candidates:
            return {"error": "no feasible route"}
            
        # Select the optimum stop: the cheapest candidate in the window
        best_stop = min(candidates, key=lambda x: x['price'])
        chosen_stops.append(best_stop)
        
        # Advance our position to the chosen station's mileage location
        current_mileage = best_stop['route_mileage']
        
    # --- Cost Calculation Segment ---
    total_cost = 0.0
    
    # Build a sequential list of positions: [Start, Stop 1, Stop 2, ..., Finish]
    # Represented as tuples of (mileage, fuel_price_at_this_point)
    legs = [(0.0, 0.0)]  # Start at mile 0. Price is 0.0 because the first tank is free.
    for stop in chosen_stops:
        legs.append((stop['route_mileage'], stop['price']))
    legs.append((total_distance, 0.0))  # End at the finish line mileage.
    
    # Iterate through consecutive pairs to compute leg distances and fuel prices
    for i in range(len(legs) - 1):
        start_mileage, purchase_price = legs[i]
        end_mileage, _ = legs[i+1]
        
        leg_distance = end_mileage - start_mileage
        gallons_used = leg_distance / 10.0
        
        # The cost paid for this leg is determined by the price where the leg started
        total_cost += gallons_used * purchase_price

    return {
        "success": True,
        "total_stops": len(chosen_stops),
        "stops": chosen_stops,
        "total_cost": round(total_cost, 2)
    }