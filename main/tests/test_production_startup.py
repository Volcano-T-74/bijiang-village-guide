from pathlib import Path

from django.test import SimpleTestCase


class ProductionStartupTests(SimpleTestCase):
    def test_gunicorn_keeps_admin_responsive_during_ai_requests(self):
        start_script = (Path(__file__).resolve().parents[2] / "start.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("--threads 2", start_script)
        self.assertIn("--timeout 90", start_script)
