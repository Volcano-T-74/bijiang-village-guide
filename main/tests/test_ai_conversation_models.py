from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from main.models import AnalyticsConversation, AnalyticsTurn


class AnalyticsConversationModelTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="ai-operator", is_staff=True
        )

    def test_conversation_owns_chronological_turns_and_cascades(self):
        conversation = AnalyticsConversation.objects.create(
            owner=self.staff,
            title="最近哪个景点最受欢迎？",
            default_days=30,
        )
        first = AnalyticsTurn.objects.create(
            conversation=conversation,
            question="第一名是谁？",
            days=30,
        )
        second = AnalyticsTurn.objects.create(
            conversation=conversation,
            question="第二名呢？",
            days=30,
            status=AnalyticsTurn.Status.COMPLETED,
            answer={"summary": "第二名是古桥"},
        )

        self.assertEqual(list(conversation.turns.all()), [first, second])
        conversation.delete()
        self.assertFalse(AnalyticsTurn.objects.filter(pk__in=[first.pk, second.pk]).exists())

    def test_days_must_be_a_supported_window(self):
        conversation = AnalyticsConversation(
            owner=self.staff,
            title="测试会话",
            default_days=8,
        )
        with self.assertRaises(ValidationError):
            conversation.full_clean()

        turn = AnalyticsTurn(
            conversation=AnalyticsConversation.objects.create(
                owner=self.staff, title="有效会话", default_days=30
            ),
            question="问题",
            days=365,
        )
        with self.assertRaises(ValidationError):
            turn.full_clean()
