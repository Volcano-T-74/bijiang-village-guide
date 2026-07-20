from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from main.services.deepseek_client import (
    DeepSeekConfigurationError,
    DeepSeekResponseError,
    DeepSeekTimeoutError,
    DeepSeekUpstreamError,
)


METRICS = {
    "period": {"days": 30, "start": "2026-06-20", "end": "2026-07-20"},
    "total_sessions": 0,
    "score_formula": {"simulated_arrival": 4},
    "attractions": [],
}
ANALYSIS = {
    "summary": "村史馆最受欢迎",
    "popular_attractions": [],
    "business_recommendations": [],
    "evidence": [],
    "limitations": [],
}


class DeepSeekAnalyticsApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="analytics-admin", password="password-123"
        )
        self.user = User.objects.create_user(username="ordinary", password="password-123")

    def test_requires_staff_user(self):
        response = self.client.post("/api/v1/analytics/deepseek/", {"question": "问题"})
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.post("/api/v1/analytics/deepseek/", {"question": "问题"}).status_code,
            403,
        )

    @patch("main.api_views.analyze_visitor_metrics", return_value=ANALYSIS)
    @patch("main.api_views.build_visitor_metrics", return_value=METRICS)
    def test_admin_receives_metrics_and_analysis(self, build_metrics, analyze):
        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/v1/analytics/deepseek/",
            {"question": "最近哪个景点最受欢迎？", "days": 7},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["question"], "最近哪个景点最受欢迎？")
        self.assertEqual(response.json()["period"], METRICS["period"])
        self.assertEqual(response.json()["metrics"], METRICS)
        self.assertEqual(response.json()["analysis"], ANALYSIS)
        build_metrics.assert_called_once_with(days=7)
        analyze.assert_called_once_with("最近哪个景点最受欢迎？", METRICS)

    def test_validates_question_and_days(self):
        self.client.force_login(self.admin)
        for data in ({"question": ""}, {"question": "问题", "days": 0}, {"question": "问题", "days": 366}):
            with self.subTest(data=data):
                self.assertEqual(
                    self.client.post("/api/v1/analytics/deepseek/", data).status_code,
                    400,
                )

    def test_maps_client_errors_to_safe_statuses(self):
        self.client.force_login(self.admin)
        cases = (
            (DeepSeekConfigurationError("missing"), 503),
            (DeepSeekTimeoutError("timeout"), 504),
            (DeepSeekUpstreamError("upstream"), 502),
            (DeepSeekResponseError("invalid"), 502),
        )
        for error, expected_status in cases:
            with self.subTest(error=type(error).__name__), patch(
                "main.api_views.build_visitor_metrics", return_value=METRICS
            ), patch("main.api_views.analyze_visitor_metrics", side_effect=error):
                response = self.client.post(
                    "/api/v1/analytics/deepseek/", {"question": "问题"}
                )
                self.assertEqual(response.status_code, expected_status)
                self.assertNotIn(str(error), response.content.decode())
