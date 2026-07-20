import math

from django.core.management import call_command
from django.test import TestCase

from main.models import (
    Attraction,
    AttractionPath,
    AttractionTheme,
    StoryContent,
    Theme,
    Zone,
)


class DemoSeedTests(TestCase):
    def setUp(self):
        call_command("seed_demo_data", verbosity=0)

    def test_seed_creates_complete_nine_attraction_dataset(self):
        self.assertEqual(Zone.objects.count(), 4)
        self.assertEqual(Attraction.objects.count(), 9)
        self.assertEqual(Theme.objects.count(), 6)
        self.assertEqual(AttractionTheme.objects.count(), 21)
        self.assertEqual(StoryContent.objects.count(), 9)
        self.assertEqual(AttractionPath.objects.count(), 40)

    def test_seed_is_idempotent(self):
        call_command("seed_demo_data", verbosity=0)

        self.assertEqual(Zone.objects.count(), 4)
        self.assertEqual(Attraction.objects.count(), 9)
        self.assertEqual(Theme.objects.count(), 6)
        self.assertEqual(AttractionTheme.objects.count(), 21)
        self.assertEqual(StoryContent.objects.count(), 9)
        self.assertEqual(AttractionPath.objects.count(), 40)

    def test_cross_river_paths_only_connect_through_bridge(self):
        west = {
            "village-history-museum",
            "huang-ancestral-hall",
            "poetry-lane",
            "xiuxi-peng-ancestral-hall",
        }
        east = {
            "bixi-scholar-hall",
            "dong-ancestral-hall",
            "old-wharf",
            "waterside-ancient-tree",
        }
        direct_crossings = AttractionPath.objects.filter(
            from_attraction__slug__in=west,
            to_attraction__slug__in=east,
        ) | AttractionPath.objects.filter(
            from_attraction__slug__in=east,
            to_attraction__slug__in=west,
        )
        self.assertFalse(direct_crossings.exists())
        bridge_neighbors = set(
            AttractionPath.objects.filter(from_attraction__slug="ancient-bridge")
            .values_list("to_attraction__slug", flat=True)
        )
        self.assertEqual(bridge_neighbors, west | east)

    def test_depth_levels_theme_links_and_story_text_are_seeded(self):
        deep_slugs = set(
            Attraction.objects.filter(depth_level=2).values_list("slug", flat=True)
        )
        self.assertEqual(
            deep_slugs,
            {"village-history-museum", "huang-ancestral-hall", "ancient-bridge"},
        )
        museum = Attraction.objects.get(slug="village-history-museum")
        museum_themes = set(
            museum.theme_links.values_list("theme__name", flat=True)
        )
        self.assertEqual(museum_themes, {"岭南建筑", "宗族记忆", "古村变迁"})
        story = museum.story_contents.get(version=1)
        self.assertIn("始建于清光绪二十四年", story.full_text)
        self.assertIn("陈家祠", story.fun_fact)
        self.assertTrue(story.audio_script.startswith("村史馆坐落于"))

    def test_map_positions_and_path_formula_are_deterministic(self):
        museum = Attraction.objects.get(slug="village-history-museum")
        bridge = Attraction.objects.get(slug="ancient-bridge")
        self.assertEqual(float(museum.map_x_percent), 42.0)
        self.assertEqual(float(museum.map_y_percent), 13.0)

        path = AttractionPath.objects.get(
            from_attraction=museum, to_attraction=bridge
        )
        raw_distance = math.hypot(42 - 50, 13 - 45) * 7
        expected_distance = max(80, int(raw_distance / 10 + 0.5) * 10)
        self.assertEqual(path.distance_meters, expected_distance)
        self.assertEqual(
            path.estimated_minutes, math.ceil(expected_distance / 75)
        )
        scenic = AttractionPath.objects.get(
            from_attraction=bridge,
            to_attraction__slug="old-wharf",
        )
        self.assertTrue(scenic.is_scenic_route)

    def test_zone_centers_are_optional_for_demo_topology(self):
        zone = Zone.objects.get(zone_name="文乡雅集区")
        self.assertIsNone(zone.center_latitude)
        self.assertIsNone(zone.center_longitude)
