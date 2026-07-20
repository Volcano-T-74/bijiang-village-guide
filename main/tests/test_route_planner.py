from django.core.management import call_command
from django.test import TestCase

from main.models import AttractionPath


class RoutePlannerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)

    def test_routes_respect_duration_start_and_uniqueness(self):
        from main.services.route_planner import generate_route

        for duration in (30, 60, 90):
            with self.subTest(duration=duration):
                route = generate_route(["岭南建筑"], duration, "relaxed")
                slugs = [stop["slug"] for stop in route["stops"]]
                self.assertEqual(slugs[0], "village-history-museum")
                self.assertEqual(len(slugs), len(set(slugs)))
                self.assertLessEqual(route["total_estimated_minutes"], duration)

    def test_different_interests_produce_relevant_different_routes(self):
        from main.services.route_planner import generate_route

        architecture = generate_route(["岭南建筑"], 30, "relaxed")
        waterfront = generate_route(["自然水岸"], 30, "relaxed")
        architecture_slugs = [item["slug"] for item in architecture["stops"]]
        waterfront_slugs = [item["slug"] for item in waterfront["stops"]]

        self.assertNotEqual(architecture_slugs, waterfront_slugs)
        self.assertTrue(
            any("岭南建筑" in item["matched_themes"] for item in architecture["stops"])
        )
        self.assertTrue(
            any("自然水岸" in item["matched_themes"] for item in waterfront["stops"])
        )

    def test_deep_mode_prioritizes_multiple_depth_two_attractions(self):
        from main.services.route_planner import generate_route

        route = generate_route(["岭南建筑", "诗书文脉"], 60, "deep")
        deep_count = sum(item["depth_level"] == 2 for item in route["stops"])
        self.assertGreaterEqual(deep_count, 2)

    def test_same_input_is_deterministic(self):
        from main.services.route_planner import generate_route

        first = generate_route(["宗族记忆"], 60, "relaxed")
        second = generate_route(["宗族记忆"], 60, "relaxed")
        self.assertEqual(first, second)

    def test_missing_path_data_raises_no_route_error(self):
        from main.services.route_planner import NoRouteError, generate_route

        AttractionPath.objects.all().delete()
        with self.assertRaises(NoRouteError):
            generate_route(["岭南建筑"], 60, "relaxed")

    def test_cross_river_route_uses_ancient_bridge(self):
        from main.services.route_planner import generate_route

        route = generate_route(
            [],
            90,
            "relaxed",
            start_attraction_slug="village-history-museum",
            visited_attraction_slugs={
                "huang-ancestral-hall",
                "poetry-lane",
                "xiuxi-peng-ancestral-hall",
            },
        )
        slugs = [stop["slug"] for stop in route["stops"]]
        east = {
            "bixi-scholar-hall",
            "dong-ancestral-hall",
            "old-wharf",
            "waterside-ancient-tree",
        }
        self.assertTrue(east.intersection(slugs))
        self.assertIn("ancient-bridge", slugs)

    def test_southeast_route_follows_the_river_without_backtracking(self):
        from main.services.route_planner import generate_route

        route = generate_route([], 90, "relaxed")
        slugs = [stop["slug"] for stop in route["stops"]]
        southeast = [
            slug
            for slug in slugs
            if slug
            in {
                "dong-ancestral-hall",
                "old-wharf",
                "waterside-ancient-tree",
            }
        ]
        self.assertEqual(
            southeast,
            ["dong-ancestral-hall", "old-wharf", "waterside-ancient-tree"],
        )

    def test_visited_attractions_are_excluded_except_current_start(self):
        from main.services.route_planner import NoRouteError, generate_route

        with self.assertRaisesRegex(NoRouteError, "没有可继续推荐的景点"):
            generate_route(
                [],
                90,
                "relaxed",
                start_attraction_slug="huang-ancestral-hall",
                visited_attraction_slugs={
                    "village-history-museum",
                    "huang-ancestral-hall",
                },
            )
