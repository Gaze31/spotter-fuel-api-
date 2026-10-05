Spotter Fuel Route API

Given a start and finish location in the USA, returns the route, the cheapest feasible fuel stops along it (500-mile vehicle range), and the total fuel cost at 10 mpg.

Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your routing/geocoding provider details
python manage.py migrate
python manage.py load_fuel_prices data/fuel-prices-for-be-assessment.csv
python manage.py runserver
API

POST /api/route/

json
{"start": "Chicago, IL", "finish": "Denver, CO"}

Response:

json
{
  "route": {
    "distance_miles": 1005.1,
    "geometry": [[41.8781, -87.6298], ...]
  },
  "stops": [
    {"name": "QUIKTRIP #598", "latitude": 41.26, "longitude": -95.94, "price": 2.93, "route_mileage": 464.78},
    {"name": "AKAL TRAVEL CENTER", "latitude": 40.9, "longitude": -97.46, "price": 2.80, "route_mileage": 558.74}
  ],
  "total_fuel_cost": 151.67
}

A location that can't be geocoded returns 400 with an error message. A route the optimizer genuinely can't solve (no station reachable within range) returns 422.

Design decisions
Routing provider: OSRM's public routing server (router.project-osrm.org), called exactly once per request (route/services/routing.py). One live HTTP call does the whole job - route geometry, total distance, and the point-by-point path used to match fuel stations against the route. This is verified by a test (test_routing_api_called_exactly_once_per_request) that mocks the call and asserts it only fires once.
Geocoding: stations only have city/state in the source CSV, no coordinates. The 4,275 unique (city, state) pairs are geocoded once via a management command (load_fuel_prices), not per-request and not per-row - geocoding at request time would blow the response-time budget and hit rate limits on every call. Of the 8,151 stations, 7,984 successfully resolved coordinates; the remaining 167 are mostly Canadian entries and unusual location names that don't resolve against a US-only geocoder, and are simply excluded from route matching rather than causing an error.
Route-matching buffer: a station counts as "on the route" if it's within 20 miles (~0.3 degrees) of the closest point on the route path. This threshold is set deliberately loose because station coordinates are only as precise as their city center, not their actual address - a tighter threshold would silently exclude real, usable stations that happen to geocode a few miles from the highway.
Fill/cost assumption: the vehicle starts with a full tank, so the first leg of any trip is free. Every stop after that is priced at the rate of the station where it was purchased, applied to the distance of the leg it covers. This is a simplification - a real driver doesn't necessarily start full or buy a full tank at every stop - but it keeps the cost model unambiguous and auditable from the response alone.
Performance: matching every station against every route point is O(stations x route points) - with ~8,000 stations and a route geometry of several thousand points, that's tens of millions of distance calculations per request if done naively. Before the optimizer runs, RouteFuelView prefilters Station to a bounding box around the route's min/max latitude and longitude (padded by the same 20-mile margin as the matching threshold). On a real Chicago-to-Denver request this took the response time from what would otherwise be well over a minute down to 5.44 seconds, measured directly in Postman.
Testing

python manage.py test

Five tests cover: a short route needing no stops, a long route needing at least one, the fuel-cost arithmetic by hand, the no-feasible-route error path, and (via mocking) that the routing API is called exactly once per request - directly verifying one of the stated requirements.
