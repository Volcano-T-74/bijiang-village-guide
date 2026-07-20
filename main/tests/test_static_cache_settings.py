import re

from django.conf import settings
from django.test import SimpleTestCase


class StaticCacheSettingsTests(SimpleTestCase):
    def test_frontend_static_files_come_only_from_vite_dist(self):
        self.assertEqual(
            settings.STATICFILES_DIRS,
            [settings.BASE_DIR / "frontend" / "dist"],
        )

    def test_vite_hashes_are_immutable_and_other_media_cache_for_a_day(self):
        self.assertEqual(settings.WHITENOISE_MAX_AGE, 86400)
        pattern = re.compile(settings.WHITENOISE_IMMUTABLE_FILE_TEST)
        self.assertIsNotNone(
            pattern.search("/static/frontend/assets/village-map-CNB4kQQA.webp")
        )
        self.assertIsNone(pattern.search("/static/audio/20260719_223040.m4a"))
