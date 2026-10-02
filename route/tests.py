from django.test import TestCase
from route.services.fuel_optimizer import optimize_fuel_stops, haversine_miles

from unittest.mock import patch
from rest_framework.test import APIClient
class RouteFuelViewTests(TestCase):
    @patch("route.services.routing.get_route")
    @patch("route.views.geocode_city_state")
    def test_routing_api_called_exactly_once_per_request(self, mock_geocode, mock_get_route):
        mock_geocode.return_value = (40.0, -90.0)

        mock_get_route.return_value = {
            "distance_miles": 300.0,
            "geometry": [(40.0, -90.0), (41.0, -91.0)],
            "route_mileages": [0.0, 300.0],
        }

        client = APIClient()
        response = client.post(
            "/api/route/",
            {"start": "Chicago, IL", "finish": "Denver, CO"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        mock_get_route.assert_called_once()

class FuelOptimizerTests(TestCase):
    
    def test_route_under_500_miles_needs_no_stops(self):
        # Make up a short route - total distance well under 500 miles.
        route_points = [(34.0522, -118.2437), (34.2000, -118.0000)]
        route_mileages = [0.0, 25.0]
        stations = []  # doesn't matter here - route is short enough to not need any

        result = optimize_fuel_stops(
            route_points=route_points,
            route_mileages=route_mileages,
            stations=stations,
            haversine_miles=haversine_miles,
        )

        self.assertEqual(result["total_stops"], 0)
        self.assertEqual(result["stops"], [])

    def test_route_over_500_miles_returns_at_least_one_stop(self):
        # Route needs to total over 500 miles.
        route_points = [
            (30.0, -100.0),   # Start: Mile 0
            (35.8, -100.0),   # Midpoint node: Mile 400
            (38.68, -100.0)   # Finish: Mile 600
        ]
        route_mileages = [0.0, 400.0, 600.0]

        stations = [
            {
                "name": "Mile 400 Fuel Oasis", 
                "latitude": 35.8, 
                "longitude": -100.0, 
                "price": 3.45
            },
        ]

        result = optimize_fuel_stops(
            route_points=route_points,
            route_mileages=route_mileages,
            stations=stations,
            haversine_miles=haversine_miles,
        )

        self.assertIn("total_stops", result)
        self.assertEqual(result["total_stops"], 1)

    def test_unreachable_destination_returns_sensible_error(self):
        route_points = [
            (30.0, -100.0),
            (35.8, -100.0),
            (38.68, -100.0),
        ]
        route_mileages = [0.0, 400.0, 600.0]
        stations = []  # no stations at all - nothing reachable anywhere

        result = optimize_fuel_stops(
            route_points=route_points,
            route_mileages=route_mileages,
            stations=stations,
            haversine_miles=haversine_miles,
        )

        self.assertIn("error", result)
        self.assertEqual(result["error"], "no feasible route")  

    def test_total_cost_matches_distance_and_mpg_math(self):
        # Fixed scoping indentation: this method now correctly lives inside the TestCase class
        route_points = [
            (30.0, -100.0),
            (35.8, -100.0),
            (38.68, -100.0),
        ]
        route_mileages = [0.0, 400.0, 600.0]
        stations = [
            {"name": "Cost Check Station", "latitude": 35.8, "longitude": -100.0, "price": 3.00},
        ]

        result = optimize_fuel_stops(
            route_points=route_points,
            route_mileages=route_mileages,
            stations=stations,
            haversine_miles=haversine_miles,
        )

        # By hand arithmetic verification:
        # Leg 1 (mile 0 -> 400): 400 miles. Uses fuel from the initial free tank. Cost = $0.00.
        # Leg 2 (mile 400 -> 600): 200 miles. 200 miles / 10 mpg = 20 gallons used.
        # Purchased at the mile 400 station rate: 20 gallons * $3.00/gal = $60.00.
        expected_cost = 60.00
        
        self.assertIn("total_cost", result)
        self.assertAlmostEqual(result["total_cost"], expected_cost, places=2)