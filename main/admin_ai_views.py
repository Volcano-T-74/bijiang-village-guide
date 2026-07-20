from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST

from main.forms import AnalyticsConversationForm, AnalyticsQuestionForm
from main.models import AnalyticsConversation, AnalyticsTurn
from main.services.analytics_conversation import (
    ask_analytics_question,
    retry_analytics_turn,
)


ERROR_HTTP_STATUSES = {
    "configuration": 503,
    "timeout": 504,
    "authentication": 502,
    "balance": 402,
    "rate_limit": 429,
    "network": 502,
    "upstream": 502,
    "response": 502,
}


def _conversation_for_user(user, conversation_id):
    return get_object_or_404(
        AnalyticsConversation, pk=conversation_id, owner=user
    )


def _turn_payload(turn):
    return {
        "id": turn.id,
        "question": turn.question,
        "answer": turn.answer,
        "days": turn.days,
        "status": turn.status,
        "error_code": turn.error_code,
        "model": turn.model,
        "created_at": turn.created_at.isoformat(),
        "answered_at": turn.answered_at.isoformat() if turn.answered_at else None,
    }


def _conversation_payload(conversation, include_turns=False):
    payload = {
        "id": conversation.id,
        "title": conversation.title,
        "default_days": conversation.default_days,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }
    if include_turns:
        payload["turns"] = [_turn_payload(turn) for turn in conversation.turns.all()]
    return payload


def _turn_response(turn):
    payload = {"status": turn.status, "data": _turn_payload(turn)}
    if turn.status == AnalyticsTurn.Status.FAILED:
        payload["error"] = turn.error_code
        return JsonResponse(
            payload, status=ERROR_HTTP_STATUSES.get(turn.error_code, 502)
        )
    return JsonResponse(payload)


@require_GET
def ai_analytics_page(request):
    return redirect("admin_data_overview")


@require_POST
def create_conversation(request):
    form = AnalyticsConversationForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {"status": "invalid", "errors": form.errors.get_json_data()},
            status=400,
        )
    conversation = AnalyticsConversation.objects.create(
        owner=request.user,
        title="新对话",
        default_days=form.cleaned_data["default_days"],
    )
    return JsonResponse(
        {"status": "created", "data": _conversation_payload(conversation)},
        status=201,
    )


@require_GET
def conversation_detail(request, conversation_id):
    conversation = _conversation_for_user(request.user, conversation_id)
    return JsonResponse(
        {"status": "ok", "data": _conversation_payload(conversation, include_turns=True)}
    )


@require_POST
def ask_conversation(request, conversation_id):
    conversation = _conversation_for_user(request.user, conversation_id)
    form = AnalyticsQuestionForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {"status": "invalid", "errors": form.errors.get_json_data()},
            status=400,
        )
    question = form.cleaned_data["question"]
    days = form.cleaned_data["days"]
    is_first_turn = not conversation.turns.exists()
    turn = ask_analytics_question(conversation, question, days)
    conversation.default_days = days
    update_fields = ["default_days", "updated_at"]
    if is_first_turn:
        conversation.title = question[:60]
        update_fields.append("title")
    conversation.save(update_fields=update_fields)
    return _turn_response(turn)


@require_POST
def retry_turn(request, turn_id):
    turn = get_object_or_404(
        AnalyticsTurn.objects.select_related("conversation"),
        pk=turn_id,
        conversation__owner=request.user,
    )
    return _turn_response(retry_analytics_turn(turn))
