from django.urls import path

from main.api_views import (
    AttractionDetailView,
    BootstrapView,
    ItineraryDetailView,
    ItineraryGenerateView,
    SessionCreateView,
)


urlpatterns = [
    path("bootstrap/", BootstrapView.as_view(), name="api-bootstrap"),
    path(
        "attractions/<slug:slug>/",
        AttractionDetailView.as_view(),
        name="api-attraction-detail",
    ),
    path("sessions/", SessionCreateView.as_view(), name="api-session-create"),
    path(
        "itineraries/generate/",
        ItineraryGenerateView.as_view(),
        name="api-itinerary-generate",
    ),
    path(
        "itineraries/<int:itinerary_id>/",
        ItineraryDetailView.as_view(),
        name="api-itinerary-detail",
    ),
]
