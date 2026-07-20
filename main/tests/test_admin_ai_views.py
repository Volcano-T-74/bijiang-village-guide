from unittest.mock import patch
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main.models import AnalyticsConversation, AnalyticsTurn


ANALYSIS = {
    "summary": "村史馆最受欢迎",
    "popular_attractions": [],
    "business_recommendations": [],
    "evidence": ["模拟到达次数最多"],
    "limitations": ["样本量较少"],
}


class AdminAiViewsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username="staff-one", is_staff=True)
        self.other_staff = User.objects.create_user(username="staff-two", is_staff=True)
        self.ordinary = User.objects.create_user(username="ordinary")
        self.conversation = AnalyticsConversation.objects.create(
            owner=self.staff, title="我的运营分析", default_days=30
        )
        self.other_conversation = AnalyticsConversation.objects.create(
            owner=self.other_staff, title="其他人的分析", default_days=30
        )

    def test_page_requires_staff_and_lists_only_owned_conversations(self):
        response = self.client.get("/admin/ai-analytics/")
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

        self.client.force_login(self.ordinary)
        self.assertEqual(self.client.get("/admin/ai-analytics/").status_code, 302)

        self.client.force_login(self.staff)
        response = self.client.get("/admin/ai-analytics/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "我的运营分析")
        self.assertNotContains(response, "其他人的分析")

    def test_page_renders_accessible_conversation_controls(self):
        self.client.force_login(self.staff)

        response = self.client.get("/admin/ai-analytics/")

        self.assertContains(response, 'id="ai-conversation-list"', html=False)
        self.assertContains(response, 'data-delete-conversation="', html=False)
        self.assertContains(response, 'id="ai-new-conversation"', html=False)
        self.assertContains(response, 'id="ai-days"', html=False)
        self.assertContains(response, '<option value="7">最近 7 天</option>', html=True)
        self.assertContains(response, '<option value="30" selected>最近 30 天</option>', html=True)
        self.assertContains(response, '<option value="90">最近 90 天</option>', html=True)
        self.assertContains(response, 'id="ai-question"', html=False)
        self.assertContains(response, 'id="ai-send"', html=False)
        self.assertContains(response, 'aria-live="polite"', html=False)
        self.assertContains(response, "最近30天哪个景点最受欢迎？")
        self.assertContains(response, "main/admin_ai.css")
        self.assertContains(response, "main/admin_ai.js")
        self.assertContains(response, "admin_ai.css?v=")
        self.assertContains(response, "admin_ai.js?v=")

    def test_conversation_detail_enforces_ownership(self):
        self.client.force_login(self.staff)
        own = self.client.get(
            f"/admin/ai-analytics/conversations/{self.conversation.pk}/"
        )
        other = self.client.get(
            f"/admin/ai-analytics/conversations/{self.other_conversation.pk}/"
        )
        self.assertEqual(own.status_code, 200)
        self.assertEqual(own.json()["data"]["title"], "我的运营分析")
        self.assertEqual(other.status_code, 404)

    def test_deletes_only_owned_conversation_and_its_turns(self):
        turn = AnalyticsTurn.objects.create(
            conversation=self.conversation,
            question="待删除问题",
            days=30,
        )
        self.client.force_login(self.staff)

        deleted = self.client.post(
            f"/admin/ai-analytics/conversations/{self.conversation.pk}/delete/"
        )
        forbidden = self.client.post(
            f"/admin/ai-analytics/conversations/{self.other_conversation.pk}/delete/"
        )

        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["data"]["id"], self.conversation.pk)
        self.assertFalse(AnalyticsConversation.objects.filter(pk=self.conversation.pk).exists())
        self.assertFalse(AnalyticsTurn.objects.filter(pk=turn.pk).exists())
        self.assertEqual(forbidden.status_code, 404)

    def test_message_grid_can_shrink_and_scroll(self):
        css = (Path(__file__).resolve().parents[1] / "static" / "main" / "admin_ai.css").read_text(
            encoding="utf-8"
        )

        self.assertRegex(css, r"(?s)\.ai-chat\s*\{[^}]*min-height:\s*0")
        self.assertRegex(css, r"(?s)\.ai-messages\s*\{[^}]*min-height:\s*0[^}]*overflow-y:\s*scroll")
        self.assertRegex(css, r"(?s)\.ai-messages\s*\{[^}]*touch-action:\s*pan-y")
        self.assertRegex(
            css,
            r"(?s)@media \(max-width: 860px\).*?\.ai-workspace\s*\{[^}]*height:\s*calc\(100dvh - 110px\)[^}]*grid-template-rows:\s*minmax\(110px, 150px\) minmax\(0, 1fr\)",
        )
        javascript = (Path(__file__).resolve().parents[1] / "static" / "main" / "admin_ai.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('messages.addEventListener("wheel"', javascript)

    def test_creates_conversation_and_validates_days(self):
        self.client.force_login(self.staff)
        created = self.client.post(
            "/admin/ai-analytics/conversations/", {"default_days": 7}
        )
        invalid = self.client.post(
            "/admin/ai-analytics/conversations/", {"default_days": 8}
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["data"]["default_days"], 7)
        self.assertEqual(invalid.status_code, 400)

    @patch("main.admin_ai_views.ask_analytics_question")
    def test_asks_question_and_serializes_completed_turn(self, ask):
        turn = AnalyticsTurn.objects.create(
            conversation=self.conversation,
            question="哪个景点最热门？",
            answer=ANALYSIS,
            days=30,
            status=AnalyticsTurn.Status.COMPLETED,
        )
        ask.return_value = turn
        self.client.force_login(self.staff)

        response = self.client.post(
            f"/admin/ai-analytics/conversations/{self.conversation.pk}/ask/",
            {"question": "哪个景点最热门？", "days": 30},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["answer"], ANALYSIS)
        ask.assert_called_once_with(self.conversation, "哪个景点最热门？", 30)

    @patch("main.admin_ai_views.ask_analytics_question")
    def test_rejects_invalid_question_without_calling_service(self, ask):
        self.client.force_login(self.staff)
        response = self.client.post(
            f"/admin/ai-analytics/conversations/{self.conversation.pk}/ask/",
            {"question": "", "days": 30},
        )
        self.assertEqual(response.status_code, 400)
        ask.assert_not_called()

    @patch("main.admin_ai_views.ask_analytics_question")
    def test_failed_turn_returns_safe_status(self, ask):
        turn = AnalyticsTurn.objects.create(
            conversation=self.conversation,
            question="问题",
            days=30,
            status=AnalyticsTurn.Status.FAILED,
        )
        self.client.force_login(self.staff)
        cases = {
            "timeout": 504,
            "authentication": 502,
            "balance": 402,
            "rate_limit": 429,
            "network": 502,
            "upstream": 502,
        }
        for error_code, expected_status in cases.items():
            with self.subTest(error_code=error_code):
                turn.error_code = error_code
                turn.save(update_fields=("error_code",))
                ask.return_value = turn
                response = self.client.post(
                    f"/admin/ai-analytics/conversations/{self.conversation.pk}/ask/",
                    {"question": "问题", "days": 30},
                )
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(response.json()["error"], error_code)
                self.assertNotIn("exception", response.content.decode().lower())

    @patch("main.admin_ai_views.retry_analytics_turn")
    def test_retry_enforces_turn_ownership(self, retry):
        other_turn = AnalyticsTurn.objects.create(
            conversation=self.other_conversation,
            question="其他人的问题",
            days=30,
            status=AnalyticsTurn.Status.FAILED,
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            f"/admin/ai-analytics/turns/{other_turn.pk}/retry/"
        )
        self.assertEqual(response.status_code, 404)
        retry.assert_not_called()
