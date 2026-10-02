from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    """
    What the client sends in. Keeping start/finish as free-text addresses
    (e.g. "Chicago, IL") pushes the coordinate lookup onto your geocoding
    step in services/geocoding.py - TODO decide if you want to accept raw
    lat/lon instead to dodge that call entirely. Either is a defensible
    choice; just say which you picked and why in the README.
    """

    start = serializers.CharField()
    finish = serializers.CharField()


# TODO: define the response shape once you've built the view. Something
# like: route geometry, total distance, list of chosen stops (name, city,
# state, price, gallons purchased there), and total fuel cost. Whether you
# formalize that as a serializer or just build a dict in the view is your
# call - don't over-engineer the output side of a take-home.
