import json

from django.core.management import call_command
from django.test import TestCase

from main.models import AttractionPath, Itinerary, VisitorSession


class TourismApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)

    def create_session(self):
        response = self.client.post(
            "/api/v1/sessions/", data="{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def test_bootstrap_returns_real_seeded_data(self):
        response = self.client.get("/api/v1/bootstrap/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["zones"]), 4)
        self.assertEqual(len(payload["themes"]), 6)
        self.assertEqual(len(payload["attractions"]), 9)
        self.assertEqual(payload["attractions"][0]["slug"], "village-history-museum")
        self.assertEqual(payload["attractions"][0]["map_position"], {"x": 40.0, "y": 10.0})

    def test_attraction_detail_returns_latest_story(self):
        response = self.client.get(
            "/api/v1/attractions/village-history-museum/"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["name"], "村史馆")
        self.assertEqual(payload["story"]["version"], 1)
        self.assertIn("慕堂苏公祠", payload["story"]["full_text"])

    def test_session_creation_persists_anonymous_uuid(self):
        session_id = self.create_session()
        self.assertTrue(VisitorSession.objects.filter(pk=session_id).exists())

    def test_generate_and_get_itinerary(self):
        session_id = self.create_session()
        request_body = {
            "preference_tags": ["岭南建筑", "诗书文脉"],
            "duration_minutes": 60,
            "mode": "deep",
            "start_attraction_slug": "village-history-museum",
        }
        generated = self.client.post(
            "/api/v1/itineraries/generate/",
            data=json.dumps(request_body),
            content_type="application/json",
            HTTP_X_VISITOR_SESSION_ID=session_id,
        )

        self.assertEqual(generated.status_code, 201)
        payload = generated.json()
        self.assertLessEqual(payload["total_estimated_minutes"], 60)
        self.assertEqual(payload["stops"][0]["slug"], "village-history-museum")
        self.assertTrue(payload["legs"])
        self.assertTrue(payload["narrative_bridge"])
        self.assertEqual(Itinerary.objects.count(), 1)

        fetched = self.client.get(
            f"/api/v1/itineraries/{payload['id']}/",
            HTTP_X_VISITOR_SESSION_ID=session_id,
        )
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["attraction_sequence"], payload["attraction_sequence"])
        self.assertEqual(fetched.json()["score"], payload["score"])

    def test_invalid_requests_have_explicit_status_codes(self):
        session_id = self.create_session()
        invalid_theme = self.client.post(
            "/api/v1/itineraries/generate/",
            data=json.dumps(
                {
                    "preference_tags": ["不存在的主题"],
                    "duration_minutes": 60,
                    "mode": "relaxed",
                }
            ),
            content_type="application/json",
            HTTP_X_VISITOR_SESSION_ID=session_id,
        )
        self.assertEqual(invalid_theme.status_code, 400)

        invalid_session = self.client.post(
            "/api/v1/itineraries/generate/",
            data=json.dumps(
                {
                    "preference_tags": ["岭南建筑"],
                    "duration_minutes": 60,
                    "mode": "relaxed",
                }
            ),
            content_type="application/json",
            HTTP_X_VISITOR_SESSION_ID="00000000-0000-0000-0000-000000000000",
        )
        self.assertEqual(invalid_session.status_code, 404)

        AttractionPath.objects.all().delete()
        no_route = self.client.post(
            "/api/v1/itineraries/generate/",
            data=json.dumps(
                {
                    "preference_tags": ["岭南建筑"],
                    "duration_minutes": 60,
                    "mode": "relaxed",
                }
            ),
            content_type="application/json",
            HTTP_X_VISITOR_SESSION_ID=session_id,
        )
        self.assertEqual(no_route.status_code, 422)
