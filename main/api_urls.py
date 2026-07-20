from django.urls import path

from main.api_views import (
    AttractionDetailView,
    BootstrapView,
    EventCreateView,
    FavoriteCreateView,
    FootprintCreateView,
    ItineraryDetailView,
    ItineraryGenerateView,
    LocalVoiceListView,
    SessionCreateView,
)


urlpatterns = [
    path("bootstrap/", BootstrapView.as_view(), name="api-bootstrap"),
    path("local-voices/", LocalVoiceListView.as_view(), name="api-local-voices"),
    path("events/", EventCreateView.as_view(), name="api-event-create"),
    path("favorites/", FavoriteCreateView.as_view(), name="api-favorite-create"),
    path("footprints/", FootprintCreateView.as_view(), name="api-footprint-create"),
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
