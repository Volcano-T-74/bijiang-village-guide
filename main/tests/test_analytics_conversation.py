from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from main.models import AnalyticsConversation, AnalyticsTurn
from main.services.analytics_conversation import (
    ask_analytics_question,
    retry_analytics_turn,
)
from main.services.deepseek_client import (
    DeepSeekConfigurationError,
    DeepSeekResponseError,
    DeepSeekTimeoutError,
    DeepSeekUpstreamError,
)


METRICS = {
    "period": {"days": 30, "start": "2026-06-20", "end": "2026-07-20"},
    "attractions": [],
}
ANALYSIS = {
    "summary": "村史馆最受欢迎",
    "popular_attractions": [],
    "business_recommendations": [],
    "evidence": ["模拟到达次数最多"],
    "limitations": ["当前样本量较少"],
}


@override_settings(DEEPSEEK_MODEL="deepseek-chat")
class AnalyticsConversationServiceTests(TestCase):
    def setUp(self):
        staff = get_user_model().objects.create_user(
            username="conversation-service", is_staff=True
        )
        self.conversation = AnalyticsConversation.objects.create(
            owner=staff, title="运营分析", default_days=30
        )

    @patch("main.services.analytics_conversation.analyze_visitor_metrics", return_value=ANALYSIS)
    @patch("main.services.analytics_conversation.build_visitor_metrics", return_value=METRICS)
    def test_saves_success_and_uses_latest_six_completed_turns(self, build_metrics, analyze):
        completed = []
        for number in range(7):
            completed.append(
                AnalyticsTurn.objects.create(
                    conversation=self.conversation,
                    question=f"历史问题{number}",
                    answer={**ANALYSIS, "summary": f"历史回答{number}"},
                    days=30,
                    status=AnalyticsTurn.Status.COMPLETED,
                )
            )
        AnalyticsTurn.objects.create(
            conversation=self.conversation,
            question="失败问题",
            days=30,
            status=AnalyticsTurn.Status.FAILED,
            error_code="timeout",
        )

        turn = ask_analytics_question(self.conversation, "第二名呢？", 30)

        turn.refresh_from_db()
        self.assertEqual(turn.status, AnalyticsTurn.Status.COMPLETED)
        self.assertEqual(turn.answer, ANALYSIS)
        self.assertEqual(turn.metrics_snapshot, METRICS)
        self.assertEqual(turn.model, "deepseek-chat")
        self.assertIsNotNone(turn.answered_at)
        build_metrics.assert_called_once_with(days=30)
        history = analyze.call_args.kwargs["history"]
        self.assertEqual(
            [item["question"] for item in history],
            [item.question for item in completed[-6:]],
        )

    @patch("main.services.analytics_conversation.build_visitor_metrics", return_value=METRICS)
    def test_maps_failures_without_storing_exception_text(self, build_metrics):
        cases = (
            (DeepSeekConfigurationError("secret config detail"), "configuration"),
            (DeepSeekTimeoutError("secret timeout detail"), "timeout"),
            (DeepSeekUpstreamError("secret upstream detail"), "upstream"),
            (DeepSeekResponseError("secret response detail"), "response"),
        )
        for error, code in cases:
            with self.subTest(code=code), patch(
                "main.services.analytics_conversation.analyze_visitor_metrics",
                side_effect=error,
            ):
                turn = ask_analytics_question(self.conversation, f"问题-{code}", 30)
                self.assertEqual(turn.status, AnalyticsTurn.Status.FAILED)
                self.assertEqual(turn.error_code, code)
                self.assertEqual(turn.answer, {})
                self.assertNotIn("secret", str(turn.__dict__))

    @patch("main.services.analytics_conversation.analyze_visitor_metrics", return_value=ANALYSIS)
    @patch("main.services.analytics_conversation.build_visitor_metrics", return_value=METRICS)
    def test_retry_updates_the_existing_failed_turn(self, build_metrics, analyze):
        turn = AnalyticsTurn.objects.create(
            conversation=self.conversation,
            question="请重试",
            days=30,
            status=AnalyticsTurn.Status.FAILED,
            error_code="timeout",
        )

        retried = retry_analytics_turn(turn)

        self.assertEqual(retried.pk, turn.pk)
        self.assertEqual(AnalyticsTurn.objects.count(), 1)
        self.assertEqual(retried.status, AnalyticsTurn.Status.COMPLETED)
        self.assertEqual(retried.error_code, "")
        self.assertEqual(retried.answer, ANALYSIS)
