from django.db import models
from django.test import SimpleTestCase

from main.models import (
    Attraction,
    AttractionPath,
    AttractionTheme,
    AudioAsset,
    Favorite,
    Footprint,
    HiddenDetail,
    Itinerary,
    LocalVoice,
    StoryContent,
    Theme,
    Touchpoint,
    VisitorSession,
    Zone,
)


class LocalVoiceTests(SimpleTestCase):
    def test_model_contract(self):
        expected_fields = {
            "title": (models.CharField, 100),
            "original_file_name": (models.CharField, 100),
            "file_url": (models.TextField, None),
            "duration_seconds": (models.PositiveIntegerField, None),
            "language": (models.CharField, 20),
            "language_label": (models.CharField, 20),
            "display_order": (models.PositiveSmallIntegerField, None),
            "is_active": (models.BooleanField, None),
        }

        for field_name, (field_type, max_length) in expected_fields.items():
            with self.subTest(field=field_name):
                field = LocalVoice._meta.get_field(field_name)
                self.assertIsInstance(field, field_type)
                self.assertEqual(field.max_length, max_length)

        self.assertTrue(LocalVoice._meta.get_field("original_file_name").unique)
        self.assertEqual(LocalVoice._meta.get_field("language").default, "local")
        self.assertEqual(
            LocalVoice._meta.get_field("language_label").default, "当地讲述"
        )
        self.assertEqual(LocalVoice._meta.get_field("display_order").default, 0)
        self.assertIs(LocalVoice._meta.get_field("is_active").default, True)

    def test_model_metadata_and_string_representation(self):
        voice = LocalVoice(title="碧江乡音")

        self.assertEqual(LocalVoice._meta.db_table, "local_voices")
        self.assertEqual(LocalVoice._meta.ordering, ("display_order", "id"))
        self.assertEqual(LocalVoice._meta.verbose_name, "当地声音")
        self.assertEqual(LocalVoice._meta.verbose_name_plural, "当地声音")
        self.assertEqual(str(voice), "碧江乡音")


class DomainModelContractTests(SimpleTestCase):
    def test_all_required_tables_have_explicit_names(self):
        expected = {
            Zone: "zones",
            Attraction: "attractions",
            StoryContent: "story_contents",
            AudioAsset: "audio_assets",
            Theme: "themes",
            AttractionTheme: "attraction_themes",
            HiddenDetail: "hidden_details",
            AttractionPath: "attraction_paths",
            Touchpoint: "touchpoints",
            VisitorSession: "visitor_sessions",
            Itinerary: "itineraries",
            Footprint: "footprints",
            Favorite: "favorites",
        }

        for model, table_name in expected.items():
            with self.subTest(model=model.__name__):
                self.assertEqual(model._meta.db_table, table_name)

    def test_primary_keys_match_serial_uuid_and_bigserial_requirements(self):
        self.assertIsInstance(Attraction._meta.pk, models.AutoField)
        self.assertIsInstance(VisitorSession._meta.pk, models.UUIDField)
        self.assertIsInstance(Footprint._meta.pk, models.BigAutoField)

    def test_attraction_contract(self):
        zone = Attraction._meta.get_field("zone")
        self.assertIs(zone.remote_field.model, Zone)
        self.assertIs(zone.remote_field.on_delete, models.PROTECT)
        self.assertTrue(Attraction._meta.get_field("slug").unique)
        self.assertTrue(Attraction._meta.get_field("latitude").null)
        self.assertTrue(Attraction._meta.get_field("longitude").null)
        constraint_names = {item.name for item in Attraction._meta.constraints}
        self.assertIn("attractions_depth_level_valid", constraint_names)
        self.assertIn("attractions_status_valid", constraint_names)

    def test_content_and_audio_relationships(self):
        attraction = StoryContent._meta.get_field("attraction")
        content = AudioAsset._meta.get_field("content")
        self.assertIs(attraction.remote_field.model, Attraction)
        self.assertIs(content.remote_field.model, StoryContent)
        self.assertEqual(AudioAsset._meta.get_field("language").default, "zh-CN")
        constraint_names = {item.name for item in StoryContent._meta.constraints}
        self.assertIn("story_contents_attraction_version_unique", constraint_names)

    def test_join_path_and_favorite_uniqueness_constraints_exist(self):
        checks = {
            AttractionTheme: "attraction_themes_pair_unique",
            AttractionPath: "attraction_paths_pair_unique",
            Favorite: "favorites_session_attraction_unique",
        }
        for model, name in checks.items():
            with self.subTest(model=model.__name__):
                self.assertIn(name, {item.name for item in model._meta.constraints})

    def test_session_and_itinerary_json_fields(self):
        self.assertIsInstance(
            VisitorSession._meta.get_field("preference_tags"), models.JSONField
        )
        self.assertIsInstance(
            Itinerary._meta.get_field("zone_sequence"), models.JSONField
        )
        self.assertIsInstance(
            Itinerary._meta.get_field("narrative_bridge"), models.JSONField
        )
        last_zone = VisitorSession._meta.get_field("last_known_zone")
        self.assertTrue(last_zone.null)
        self.assertIs(last_zone.remote_field.on_delete, models.SET_NULL)

    def test_touchpoint_trigger_code_is_unique(self):
        self.assertTrue(Touchpoint._meta.get_field("trigger_code").unique)

    def test_footprint_keeps_all_trigger_relationships(self):
        targets = {
            "session": VisitorSession,
            "itinerary": Itinerary,
            "attraction": Attraction,
            "touchpoint": Touchpoint,
        }
        for field_name, target in targets.items():
            with self.subTest(field=field_name):
                field = Footprint._meta.get_field(field_name)
                self.assertIs(field.remote_field.model, target)
