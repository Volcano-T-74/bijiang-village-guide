import json
import socket
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from main.services.deepseek_client import (
    DeepSeekConfigurationError,
    DeepSeekResponseError,
    DeepSeekTimeoutError,
    DeepSeekUpstreamError,
    analyze_visitor_metrics,
)


METRICS = {
    "period": {"days": 30, "start": "2026-06-20", "end": "2026-07-20"},
    "total_sessions": 2,
    "attractions": [
        {
            "name": "村史馆",
            "slug": "village-history-museum",
            "simulated_arrivals": 2,
            "footprints": 1,
            "favorites": 1,
            "route_appearances": 1,
            "event_count": 3,
            "popularity_score": 14,
        }
    ],
}

ANALYSIS = {
    "summary": "村史馆最热门",
    "popular_attractions": [{"slug": "village-history-museum", "reason": "到达最多"}],
    "business_recommendations": [{"location": "村史馆", "suggestion": "设置文创摊"}],
    "evidence": ["模拟到达2次"],
    "limitations": ["样本量较小"],
}


def mock_response(payload):
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return response


@override_settings(
    DEEPSEEK_API_KEY="test-key",
    DEEPSEEK_MODEL="deepseek-chat",
    DEEPSEEK_BASE_URL="https://api.deepseek.com",
    DEEPSEEK_TIMEOUT_SECONDS=12,
)
class DeepSeekClientTests(SimpleTestCase):
    @patch("main.services.deepseek_client.urlopen")
    def test_includes_prior_completed_turns_before_current_metrics(self, mocked_urlopen):
        mocked_urlopen.return_value = mock_response(
            {"choices": [{"message": {"content": json.dumps(ANALYSIS, ensure_ascii=False)}}]}
        )
        history = [{"question": "第一名是谁？", "answer": ANALYSIS}]

        analyze_visitor_metrics("第二名呢？", METRICS, history=history)

        request = mocked_urlopen.call_args.args[0]
        messages = json.loads(request.data.decode("utf-8"))["messages"]
        self.assertEqual([item["role"] for item in messages], ["system", "user", "assistant", "user"])
        self.assertEqual(messages[1]["content"], "第一名是谁？")
        self.assertEqual(json.loads(messages[2]["content"]), ANALYSIS)
        current = json.loads(messages[3]["content"])
        self.assertEqual(current, {"question": "第二名呢？", "metrics": METRICS})

    @patch("main.services.deepseek_client.urlopen")
    def test_returns_structured_analysis_without_sending_private_identifiers(self, mocked_urlopen):
        mocked_urlopen.return_value = mock_response(
            {"choices": [{"message": {"content": json.dumps(ANALYSIS, ensure_ascii=False)}}]}
        )

        result = analyze_visitor_metrics("哪个景点最热门？", METRICS)

        self.assertEqual(result, ANALYSIS)
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(payload["model"], "deepseek-chat")
        self.assertNotIn("response_format", payload)
        self.assertNotIn("00000000-0000-0000-0000-000000000000", request.data.decode())
        self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], 12)

    @patch("main.services.deepseek_client.urlopen")
    def test_accepts_json_inside_markdown_code_fence(self, mocked_urlopen):
        fenced = f"```json\n{json.dumps(ANALYSIS, ensure_ascii=False)}\n```"
        mocked_urlopen.return_value = mock_response(
            {"choices": [{"message": {"content": fenced}}]}
        )

        result = analyze_visitor_metrics("问题", METRICS)

        self.assertEqual(result, ANALYSIS)

    @override_settings(DEEPSEEK_TIMEOUT_SECONDS=120)
    @patch("main.services.deepseek_client.urlopen")
    def test_caps_provider_timeout_below_gunicorn_timeout(self, mocked_urlopen):
        mocked_urlopen.return_value = mock_response(
            {"choices": [{"message": {"content": json.dumps(ANALYSIS)}}]}
        )

        analyze_visitor_metrics("问题", METRICS)

        self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], 60)

    @override_settings(DEEPSEEK_API_KEY="")
    def test_requires_api_key(self):
        with self.assertRaises(DeepSeekConfigurationError):
            analyze_visitor_metrics("问题", METRICS)

    @patch("main.services.deepseek_client.urlopen", side_effect=socket.timeout())
    def test_maps_timeout(self, mocked_urlopen):
        with self.assertRaises(DeepSeekTimeoutError):
            analyze_visitor_metrics("问题", METRICS)

    @patch("main.services.deepseek_client.urlopen")
    def test_maps_http_error_without_exposing_response_body(self, mocked_urlopen):
        for status_code in (401, 402, 429, 500):
            with self.subTest(status_code=status_code):
                mocked_urlopen.side_effect = HTTPError(
                    "https://api.deepseek.com/chat/completions",
                    status_code,
                    "Upstream error",
                    {},
                    BytesIO(b"secret upstream body"),
                )
                with self.assertRaisesRegex(
                    DeepSeekUpstreamError, str(status_code)
                ) as raised:
                    analyze_visitor_metrics("问题", METRICS)
                self.assertEqual(raised.exception.status_code, status_code)
                self.assertNotIn("secret upstream body", str(raised.exception))

    @patch("main.services.deepseek_client.urlopen")
    def test_rejects_invalid_or_incomplete_model_response(self, mocked_urlopen):
        for content in ("not-json", json.dumps({"summary": "missing fields"})):
            with self.subTest(content=content):
                mocked_urlopen.return_value = mock_response(
                    {"choices": [{"message": {"content": content}}]}
                )
                with self.assertRaises(DeepSeekResponseError):
                    analyze_visitor_metrics("问题", METRICS)
