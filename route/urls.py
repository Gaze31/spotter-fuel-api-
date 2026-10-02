from django.urls import path

from route.views import RouteFuelView

urlpatterns = [
    path("route/", RouteFuelView.as_view(), name="route-fuel"),
]
