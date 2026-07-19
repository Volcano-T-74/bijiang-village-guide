import json

from django.core.management import call_command
from django.test import TestCase

from main.models import Favorite, Footprint, Itinerary, VisitorEvent, VisitorSession


class BehaviorApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)

    def create_session(self):
        response = self.client.post(
            "/api/v1/sessions/", data="{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def create_itinerary(self, session_id):
        response = self.client.post(
            "/api/v1/itineraries/generate/",
            data=json.dumps(
                {
                    "preference_tags": [],
                    "duration_minutes": 60,
                    "mode": "relaxed",
                    "start_attraction_slug": "village-history-museum",
                }
            ),
            content_type="application/json",
            HTTP_X_VISITOR_SESSION_ID=session_id,
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def test_records_generic_frontend_event(self):
        session_id = self.create_session()

        response = self.client.post(
            "/api/v1/events/",
            data=json.dumps(
                {
                    "event_type": "audio_play",
                    "attraction_slug": "village-history-museum",
                    "metadata": {"source": "frontend"},
                }
            ),
            content_type="application/json",
            HTTP_X_VISITOR_SESSION_ID=session_id,
        )

        self.assertEqual(response.status_code, 201)
        event = VisitorEvent.objects.get()
        self.assertEqual(str(event.session_id), session_id)
        self.assertEqual(event.event_type, "audio_play")
        self.assertEqual(event.attraction.slug, "village-history-museum")
        self.assertEqual(event.metadata, {"source": "frontend"})

    def test_records_favorite_idempotently(self):
        session_id = self.create_session()

        for _ in range(2):
            response = self.client.post(
                "/api/v1/favorites/",
                data=json.dumps({"attraction_slug": "village-history-museum"}),
                content_type="application/json",
                HTTP_X_VISITOR_SESSION_ID=session_id,
            )
            self.assertEqual(response.status_code, 201)

        self.assertEqual(Favorite.objects.count(), 1)
        favorite = Favorite.objects.get()
        self.assertEqual(str(favorite.session_id), session_id)
        self.assertEqual(favorite.attraction.slug, "village-history-museum")

    def test_records_footprint_with_route_and_default_touchpoint(self):
        session_id = self.create_session()
        itinerary_id = self.create_itinerary(session_id)

        response = self.client.post(
            "/api/v1/footprints/",
            data=json.dumps(
                {
                    "itinerary_id": itinerary_id,
                    "attraction_slug": "village-history-museum",
                    "audio_played": True,
                }
            ),
            content_type="application/json",
            HTTP_X_VISITOR_SESSION_ID=session_id,
        )

        self.assertEqual(response.status_code, 201)
        footprint = Footprint.objects.get()
        self.assertEqual(str(footprint.session_id), session_id)
        self.assertEqual(footprint.itinerary_id, itinerary_id)
        self.assertEqual(footprint.attraction.slug, "village-history-museum")
        self.assertTrue(footprint.audio_played)

    def test_behavior_endpoints_require_session(self):
        response = self.client.post(
            "/api/v1/events/",
            data=json.dumps({"event_type": "page_view"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(VisitorSession.objects.count(), 0)
        self.assertEqual(Itinerary.objects.count(), 0)
