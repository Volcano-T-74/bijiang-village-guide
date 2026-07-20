from pathlib import Path

from django.test import SimpleTestCase


class ProductionStartupTests(SimpleTestCase):
    def test_gunicorn_keeps_admin_responsive_during_ai_requests(self):
        start_script = (Path(__file__).resolve().parents[2] / "start.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("--threads 2", start_script)
        self.assertIn("--timeout 90", start_script)

    def test_render_config_uses_requested_openai_compatible_provider(self):
        render_config = (Path(__file__).resolve().parents[2] / "render.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("- key: DEEPSEEK_API_KEY\n        sync: false", render_config)
        self.assertIn("- key: DEEPSEEK_MODEL\n        value: DeepSeek-V4-Pro", render_config)
        self.assertIn(
            "- key: DEEPSEEK_BASE_URL\n        value: https://api.ldwnb666.xyz/v1",
            render_config,
        )
        self.assertIn("- key: DEEPSEEK_TIMEOUT_SECONDS\n        value: \"60\"", render_config)
