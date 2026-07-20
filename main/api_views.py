from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from main.models import (
    Attraction,
    AttractionPath,
    Favorite,
    Footprint,
    Itinerary,
    LocalVoice,
    Theme,
    VisitorEvent,
    VisitorSession,
    Zone,
)
from main.serializers import (
    EventCreateSerializer,
    FavoriteCreateSerializer,
    FootprintCreateSerializer,
    ItineraryGenerateSerializer,
    SessionCreateSerializer,
    DeepSeekAnalyticsSerializer,
)
from main.services.deepseek_client import (
    DeepSeekConfigurationError,
    DeepSeekResponseError,
    DeepSeekTimeoutError,
    DeepSeekUpstreamError,
    analyze_visitor_metrics,
)
from main.services.route_planner import NoRouteError, build_route_payload, generate_route
from main.services.visitor_analytics import build_visitor_metrics


def _session_from_request(request):
    session_id = request.headers.get("X-Visitor-Session-ID")
    if not session_id:
        raise NotFound("游客会话不存在。")
    try:
        return VisitorSession.objects.get(pk=session_id)
    except (VisitorSession.DoesNotExist, ValueError):
        raise NotFound("游客会话不存在。")


def _summary(attraction):
    return {
        "id": attraction.id,
        "name": attraction.name,
        "slug": attraction.slug,
        "subtitle": attraction.subtitle,
        "type": attraction.type,
        "depth_level": attraction.depth_level,
        "cover_image_url": attraction.cover_image_url,
        "zone": {"id": attraction.zone_id, "name": attraction.zone.zone_name},
        "themes": sorted(link.theme.name for link in attraction.theme_links.all()),
        "map_position": {
            "x": float(attraction.map_x_percent),
            "y": float(attraction.map_y_percent),
        },
    }


class BootstrapView(APIView):
    def get(self, request):
        zones = Zone.objects.order_by("id")
        themes = Theme.objects.order_by("id")
        attractions = (
            Attraction.objects.filter(status=Attraction.Status.ENABLED)
            .select_related("zone")
            .prefetch_related("theme_links__theme")
            .order_by("display_order", "id")
        )
        return Response(
            {
                "zones": [
                    {
                        "id": item.id,
                        "name": item.zone_name,
                        "visual_cue": item.visual_cue,
                        "description": item.description,
                    }
                    for item in zones
                ],
                "themes": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "icon": item.icon,
                        "description": item.description,
                    }
                    for item in themes
                ],
                "attractions": [_summary(item) for item in attractions],
            }
        )


class LocalVoiceListView(APIView):
    def get(self, request):
        voices = LocalVoice.objects.filter(is_active=True).order_by(
            "display_order", "id"
        )
        return Response(
            [
                {
                    "id": item.id,
                    "title": item.title,
                    "original_file_name": item.original_file_name,
                    "file_url": item.file_url,
                    "duration_seconds": item.duration_seconds,
                    "language": item.language,
                    "language_label": item.language_label,
                }
                for item in voices
            ]
        )


class AttractionDetailView(APIView):
    def get(self, request, slug):
        attraction = get_object_or_404(
            Attraction.objects.select_related("zone").prefetch_related(
                "theme_links__theme",
                "story_contents__audio_assets",
                "hidden_details",
            ),
            slug=slug,
            status=Attraction.Status.ENABLED,
        )
        payload = _summary(attraction)
        story = max(
            attraction.story_contents.all(), key=lambda item: item.version, default=None
        )
        payload["story"] = (
            {
                "id": story.id,
                "version": story.version,
                "full_text": story.full_text,
                "audio_script": story.audio_script,
                "fun_fact": story.fun_fact,
                "audio_assets": [
                    {
                        "id": audio.id,
                        "file_name": audio.file_name,
                        "file_url": audio.file_url,
                        "duration_seconds": audio.duration_seconds,
                        "language": audio.language,
                    }
                    for audio in story.audio_assets.all()
                ],
            }
            if story
            else None
        )
        payload["hidden_details"] = [
            {
                "id": item.id,
                "detail_text": item.detail_text,
                "poi_latitude": float(item.poi_latitude),
                "poi_longitude": float(item.poi_longitude),
                "trigger_distance_meters": item.trigger_distance_meters,
            }
            for item in attraction.hidden_details.all()
        ]
        return Response(payload)


class SessionCreateView(APIView):
    def post(self, request):
        serializer = SessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = VisitorSession.objects.create(
            preference_tags=serializer.validated_data["preference_tags"]
        )
        return Response(
            {
                "id": str(session.id),
                "preference_tags": session.preference_tags,
                "created_at": session.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


def _itinerary_payload(itinerary):
    attractions = {
        item.id: item
        for item in Attraction.objects.filter(id__in=itinerary.attraction_sequence)
        .select_related("zone")
        .prefetch_related("theme_links__theme")
    }
    try:
        ordered = [attractions[item] for item in itinerary.attraction_sequence]
    except KeyError as exc:
        raise NoRouteError("路线包含已不存在的景点。") from exc
    paths = {
        (item.from_attraction_id, item.to_attraction_id): item
        for item in AttractionPath.objects.filter(
            from_attraction_id__in=itinerary.attraction_sequence,
            to_attraction_id__in=itinerary.attraction_sequence,
        )
    }
    payload = build_route_payload(
        ordered,
        itinerary.preference_tags_snapshot,
        itinerary.planning_mode,
        itinerary.total_estimated_minutes,
        itinerary.score,
        paths,
        itinerary.narrative_bridge,
    )
    payload.update(
        {
            "id": itinerary.id,
            "session_id": str(itinerary.session_id),
            "duration_limit_minutes": itinerary.duration_limit_minutes,
            "mode": itinerary.planning_mode,
            "preference_tags": itinerary.preference_tags_snapshot,
            "generated_at": itinerary.generated_at,
            "is_completed": itinerary.is_completed,
        }
    )
    return payload


class ItineraryGenerateView(APIView):
    @transaction.atomic
    def post(self, request):
        session = _session_from_request(request)
        serializer = ItineraryGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        try:
            route = generate_route(
                values["preference_tags"],
                values["duration_minutes"],
                values["mode"],
                values["start_attraction_slug"],
                values["visited_attraction_slugs"],
            )
        except NoRouteError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        itinerary = Itinerary.objects.create(
            session=session,
            zone_sequence=route["zone_sequence"],
            attraction_sequence=route["attraction_sequence"],
            narrative_bridge=route["narrative_bridge"],
            preference_tags_snapshot=values["preference_tags"],
            planning_mode=values["mode"],
            duration_limit_minutes=values["duration_minutes"],
            score=route["score"],
            total_estimated_minutes=route["total_estimated_minutes"],
        )
        session.preference_tags = values["preference_tags"]
        session.save(update_fields=("preference_tags", "last_active_at"))
        route.update(
            {
                "id": itinerary.id,
                "session_id": str(session.id),
                "duration_limit_minutes": values["duration_minutes"],
                "mode": values["mode"],
                "preference_tags": values["preference_tags"],
                "generated_at": itinerary.generated_at,
                "is_completed": itinerary.is_completed,
            }
        )
        return Response(route, status=status.HTTP_201_CREATED)


class ItineraryDetailView(APIView):
    def get(self, request, itinerary_id):
        session = _session_from_request(request)
        itinerary = get_object_or_404(
            Itinerary, pk=itinerary_id, session=session
        )
        try:
            return Response(_itinerary_payload(itinerary))
        except NoRouteError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )


class EventCreateView(APIView):
    def post(self, request):
        session = _session_from_request(request)
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        itinerary = None
        itinerary_id = serializer.validated_data.get("itinerary_id")
        if itinerary_id is not None:
            itinerary = get_object_or_404(Itinerary, pk=itinerary_id, session=session)
        event = VisitorEvent.objects.create(
            session=session,
            event_type=serializer.validated_data["event_type"],
            attraction=getattr(serializer, "attraction", None),
            itinerary=itinerary,
            metadata=serializer.validated_data["metadata"],
        )
        return Response(
            {
                "id": event.id,
                "event_type": event.event_type,
                "created_at": event.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class FavoriteCreateView(APIView):
    def post(self, request):
        session = _session_from_request(request)
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite, _ = Favorite.objects.get_or_create(
            session=session,
            attraction=serializer.attraction,
        )
        return Response(
            {
                "id": favorite.id,
                "attraction_slug": favorite.attraction.slug,
                "created_at": favorite.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class FootprintCreateView(APIView):
    def post(self, request):
        session = _session_from_request(request)
        serializer = FootprintCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        itinerary = get_object_or_404(
            Itinerary,
            pk=serializer.validated_data["itinerary_id"],
            session=session,
        )
        footprint = Footprint.objects.create(
            session=session,
            itinerary=itinerary,
            attraction=serializer.attraction,
            touchpoint=serializer.touchpoint,
            audio_played=serializer.validated_data["audio_played"],
        )
        return Response(
            {
                "id": footprint.id,
                "attraction_slug": footprint.attraction.slug,
                "touchpoint_code": footprint.touchpoint.trigger_code,
                "triggered_at": footprint.triggered_at,
                "audio_played": footprint.audio_played,
            },
            status=status.HTTP_201_CREATED,
        )


class DeepSeekAnalyticsView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = DeepSeekAnalyticsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        days = serializer.validated_data["days"]
        try:
            metrics = build_visitor_metrics(days=days)
            analysis = analyze_visitor_metrics(question, metrics)
        except DeepSeekConfigurationError:
            return Response(
                {"detail": "DeepSeek 服务尚未配置。"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DeepSeekTimeoutError:
            return Response(
                {"detail": "DeepSeek 服务响应超时，请稍后重试。"},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except (DeepSeekUpstreamError, DeepSeekResponseError):
            return Response(
                {"detail": "DeepSeek 服务暂时不可用，请稍后重试。"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            {
                "question": question,
                "period": metrics["period"],
                "metrics": metrics,
                "analysis": analysis,
                "model": settings.DEEPSEEK_MODEL,
            }
        )
