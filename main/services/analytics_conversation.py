from django.conf import settings
from django.utils import timezone

from main.models import AnalyticsTurn
from main.services.deepseek_client import (
    DeepSeekConfigurationError,
    DeepSeekResponseError,
    DeepSeekTimeoutError,
    DeepSeekUpstreamError,
    analyze_visitor_metrics,
)
from main.services.visitor_analytics import build_visitor_metrics


ERROR_CODES = {
    DeepSeekConfigurationError: "configuration",
    DeepSeekTimeoutError: "timeout",
    DeepSeekUpstreamError: "upstream",
    DeepSeekResponseError: "response",
}


def _completed_history(conversation):
    recent = list(
        conversation.turns.filter(status=AnalyticsTurn.Status.COMPLETED)
        .order_by("-created_at", "-id")[:6]
    )
    return [
        {"question": turn.question, "answer": turn.answer}
        for turn in reversed(recent)
    ]


def _run_turn(turn):
    metrics = build_visitor_metrics(days=turn.days)
    turn.metrics_snapshot = metrics
    turn.model = settings.DEEPSEEK_MODEL
    turn.save(update_fields=("metrics_snapshot", "model"))

    try:
        answer = analyze_visitor_metrics(
            turn.question,
            metrics,
            history=_completed_history(turn.conversation),
        )
    except tuple(ERROR_CODES) as exc:
        turn.status = AnalyticsTurn.Status.FAILED
        turn.answer = {}
        turn.error_code = ERROR_CODES[type(exc)]
        turn.answered_at = timezone.now()
        turn.save(
            update_fields=("status", "answer", "error_code", "answered_at")
        )
        return turn

    turn.status = AnalyticsTurn.Status.COMPLETED
    turn.answer = answer
    turn.error_code = ""
    turn.answered_at = timezone.now()
    turn.save(update_fields=("status", "answer", "error_code", "answered_at"))
    turn.conversation.save(update_fields=("updated_at",))
    return turn


def ask_analytics_question(conversation, question, days):
    turn = AnalyticsTurn.objects.create(
        conversation=conversation,
        question=question,
        days=days,
        status=AnalyticsTurn.Status.PENDING,
    )
    return _run_turn(turn)


def retry_analytics_turn(turn):
    turn.status = AnalyticsTurn.Status.PENDING
    turn.answer = {}
    turn.metrics_snapshot = {}
    turn.model = ""
    turn.error_code = ""
    turn.answered_at = None
    turn.save(
        update_fields=(
            "status",
            "answer",
            "metrics_snapshot",
            "model",
            "error_code",
            "answered_at",
        )
    )
    return _run_turn(turn)
