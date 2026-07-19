from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse


class SameOriginFrontendTests(SimpleTestCase):
    def test_root_serves_vite_entry_document(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div id="app"></div>', html=True)
        self.assertContains(response, "/static/frontend/assets/")

    def test_admin_remains_on_the_same_origin_and_requires_login(self):
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_django_reads_the_vite_build_as_template_and_static_source(self):
        build_dir = settings.BASE_DIR / "frontend" / "dist"
        template_dirs = {Path(path) for path in settings.TEMPLATES[0]["DIRS"]}
        static_sources = {Path(path) for path in settings.STATICFILES_DIRS}

        self.assertIn(build_dir, template_dirs)
        self.assertIn(build_dir, static_sources)
