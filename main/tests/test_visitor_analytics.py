import json
from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from main.models import (
    Attraction,
    AttractionPath,
    Favorite,
    Footprint,
    Itinerary,
    Touchpoint,
    VisitorEvent,
    VisitorSession,
)
from main.services.visitor_analytics import build_visitor_metrics


class VisitorAnalyticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)

    def test_builds_scored_attraction_metrics_without_private_details(self):
        now = timezone.now()
        museum = Attraction.objects.get(slug="village-history-museum")
        bridge = Attraction.objects.get(slug="ancient-bridge")
        session_one = VisitorSession.objects.create()
        session_two = VisitorSession.objects.create()
        old_session = VisitorSession.objects.create()
        Itinerary.objects.create(
            session=session_one,
            attraction_sequence=[museum.id, bridge.id],
            zone_sequence=[museum.zone_id],
            total_estimated_minutes=20,
        )
        Itinerary.objects.create(
            session=session_two,
            attraction_sequence=[bridge.id],
            zone_sequence=[bridge.zone_id],
            total_estimated_minutes=10,
        )
        touchpoint = Touchpoint.objects.create(
            attraction=museum,
            trigger_code="analytics-museum",
            trigger_type=Touchpoint.TriggerType.SIMULATE,
            physical_location="测试点",
        )
        VisitorEvent.objects.bulk_create([
            VisitorEvent(
                session=session_one,
                event_type="simulated_arrival",
                attraction=museum,
                metadata={"private": "omit-me"},
            ),
            VisitorEvent(
                session=session_two,
                event_type="simulated_arrival",
                attraction=museum,
            ),
            VisitorEvent(
                session=session_one,
                event_type="view_attraction",
                attraction=museum,
            ),
            VisitorEvent(
                session=old_session,
                event_type="simulated_arrival",
                attraction=museum,
            ),
        ])
        Favorite.objects.create(session=session_one, attraction=museum)
        Footprint.objects.create(
            session=session_one,
            itinerary=Itinerary.objects.filter(session=session_one).first(),
            attraction=museum,
            touchpoint=touchpoint,
        )

        recent = now - timedelta(days=1)
        VisitorSession.objects.filter(id__in=[session_one.id, session_two.id]).update(
            created_at=recent, last_active_at=recent
        )
        VisitorSession.objects.filter(id=old_session.id).update(
            created_at=now - timedelta(days=40), last_active_at=now - timedelta(days=40)
        )
        VisitorEvent.objects.exclude(session_id=old_session.id).update(created_at=recent)
        VisitorEvent.objects.filter(session_id=old_session.id).update(
            created_at=now - timedelta(days=40)
        )
        Itinerary.objects.filter(session_id__in=[session_one.id, session_two.id]).update(
            generated_at=recent
        )
        Footprint.objects.filter(session_id=session_one.id).update(triggered_at=recent)
        Favorite.objects.filter(session_id=session_one.id).update(created_at=recent)

        metrics = build_visitor_metrics(days=30, now=now)
        museum_metrics = next(
            item for item in metrics["attractions"] if item["slug"] == museum.slug
        )

        self.assertEqual(metrics["total_sessions"], 2)
        self.assertEqual(museum_metrics["simulated_arrivals"], 2)
        self.assertEqual(museum_metrics["footprints"], 1)
        self.assertEqual(museum_metrics["favorites"], 1)
        self.assertEqual(museum_metrics["route_appearances"], 1)
        self.assertEqual(museum_metrics["event_count"], 3)
        self.assertEqual(museum_metrics["popularity_score"], 14)
        serialized = json.dumps(metrics, ensure_ascii=False)
        self.assertNotIn(str(session_one.id), serialized)
        self.assertNotIn("omit-me", serialized)

    def test_invalid_days_are_rejected(self):
        with self.assertRaises(ValueError):
            build_visitor_metrics(days=0)
        with self.assertRaises(ValueError):
            build_visitor_metrics(days=366)
