

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from route.serializers import RouteRequestSerializer
from route.services import fuel_optimizer, routing
# Assuming geocode_city_state is imported from your geocoding module
from route.services.geocoding import geocode_city_state 
from route.models import Station


class RouteFuelView(APIView):
    """
    POST /api/route/
    body: {"start": "City, State", "finish": "City, State"}

    Orchestration only - the actual work happens in services/. Keep it
    that way; a view with the algorithm inside it is harder to test and
    harder to explain in your Loom walkthrough.
    """

    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start = serializer.validated_data["start"]
        finish = serializer.validated_data["finish"]

        # TODO 1: turn start/finish into coordinates.
        # Geocode them using our geocoding service. If a location can't be resolved,
        # return a 400 Bad Request with a clean error message instead of a silent crash.
        city_part, state_part = start.split(",")
        start_coords = geocode_city_state(city_part.strip(), state_part.strip())
        if not start_coords:
            return Response(
                {"error": f"Could not geocode start location: '{start}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        city_part, state_part = finish.split(",")
        finish_coords = geocode_city_state(city_part.strip(), state_part.strip())
        if not finish_coords:
            return Response(
                {"error": f"Could not geocode finish location: '{finish}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_lat, start_lon = start_coords
        end_lat, end_lon = finish_coords

        # TODO 2: call routing.get_route(...) exactly once to get the
        # route geometry + total distance in miles.
        try:
            route_data = routing.get_route(start_lat, start_lon, end_lat, end_lon)
            lats = [point[0] for point in route_data["geometry"]]
            lons = [point[1] for point in route_data["geometry"]]
        except Exception as e:
            return Response(
                {"error": f"Routing service failure: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        margin = 0.3  # ~20 miles in degrees, matches your threshold in fuel_optimizer.py


               # Fetch all stations that have been successfully geocoded
      
        stations = Station.objects.filter(
        latitude__range=(min_lat - margin, max_lat + margin),
        longitude__range=(min_lon - margin, max_lon + margin),
        ).exclude(latitude=None)
        station_dicts = [
            {
                "name": s.name,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "price": float(s.retail_price),  # Cast to float for JSON compatibility and math
            }
            for s in stations
        ]

        # Execute the optimization algorithm using the data from routing and stations
        result = fuel_optimizer.optimize_fuel_stops(
            route_points=route_data["geometry"],
            route_mileages=route_data["route_mileages"],
            stations=station_dicts,
            haversine_miles=fuel_optimizer.haversine_miles,
        )

        # If the optimization engine returns a routing error (e.g. no stations in range)
        if "error" in result:
            return Response(
                {"error": result["error"]},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Return the final payload matching the required structure
        return Response({
            "route": {
                "distance_miles": round(route_data["distance_miles"], 2), 
                "geometry": route_data["geometry"]
            },
            "stops": result["stops"],
            "total_fuel_cost": result["total_cost"],
        }, status=status.HTTP_200_OK)



