from django.contrib import admin
from django.shortcuts import render
from django.utils.html import format_html
from urllib.parse import urlsplit

from .models import (
    Attraction,
    AttractionPath,
    AttractionTheme,
    AnalyticsConversation,
    AudioAsset,
    Favorite,
    Footprint,
    HiddenDetail,
    Itinerary,
    LocalVoice,
    StoryContent,
    Theme,
    Touchpoint,
    VisitorEvent,
    VisitorSession,
    Zone,
)


admin.site.site_header = "碧江文旅数据后台"
admin.site.site_title = "碧江文旅后台"
admin.site.index_title = "数据管理"


def _external_link(url, label):
    if not url:
        return "未设置"
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return "地址无效"
    return format_html(
        '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
        url,
        label,
    )


def data_overview(request):
    model_stats = (
        ("zones", "区域", Zone, "/admin/main/zone/"),
        ("attractions", "景点", Attraction, "/admin/main/attraction/"),
        ("story_contents", "故事", StoryContent, "/admin/main/storycontent/"),
        ("audio_assets", "音频", AudioAsset, "/admin/main/audioasset/"),
        ("local_voices", "当地声音", LocalVoice, "/admin/main/localvoice/"),
        ("themes", "主题", Theme, "/admin/main/theme/"),
        ("attraction_themes", "主题标签", AttractionTheme, "/admin/main/attractiontheme/"),
        ("hidden_details", "隐藏彩蛋", HiddenDetail, "/admin/main/hiddendetail/"),
        ("attraction_paths", "景点路径", AttractionPath, "/admin/main/attractionpath/"),
        ("touchpoints", "触点", Touchpoint, "/admin/main/touchpoint/"),
        ("visitor_sessions", "游客会话", VisitorSession, "/admin/main/visitorsession/"),
        ("itineraries", "专属路线", Itinerary, "/admin/main/itinerary/"),
        ("footprints", "足迹", Footprint, "/admin/main/footprint/"),
        ("favorites", "收藏", Favorite, "/admin/main/favorite/"),
        ("visitor_events", "行为事件", VisitorEvent, "/admin/main/visitorevent/"),
    )
    counts = {key: model.objects.count() for key, _, model, _ in model_stats}
    context = {
        **admin.site.each_context(request),
        "title": "数据概览",
        "counts": counts,
        "stat_cards": [
            {"label": label, "count": counts[key], "url": url}
            for key, label, _, url in model_stats
        ],
        "recent_sessions": VisitorSession.objects.select_related(
            "last_known_zone"
        ).order_by("-last_active_at")[:5],
        "recent_footprints": Footprint.objects.select_related(
            "session", "attraction", "touchpoint"
        ).order_by("-triggered_at")[:5],
        "recent_favorites": Favorite.objects.select_related(
            "session", "attraction"
        ).order_by("-created_at")[:5],
        "recent_events": VisitorEvent.objects.select_related(
            "session", "attraction", "itinerary"
        ).order_by("-created_at")[:5],
        "ai_conversations": AnalyticsConversation.objects.filter(
            owner=request.user
        ).order_by("-updated_at", "-id"),
    }
    return render(request, "admin/data_overview.html", context)


class ReadOnlyEvidenceAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("id", "zone_name", "visual_cue")
    search_fields = ("zone_name", "visual_cue", "description")


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "zone",
        "type",
        "depth_level",
        "status",
        "display_order",
        "cover_link",
    )
    list_filter = ("zone", "type", "depth_level", "status")
    search_fields = ("name", "slug", "subtitle")
    autocomplete_fields = ("zone",)
    list_select_related = ("zone",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="封面图")
    def cover_link(self, obj):
        return _external_link(obj.cover_image_url, "查看封面")


@admin.register(StoryContent)
class StoryContentAdmin(admin.ModelAdmin):
    list_display = ("id", "attraction", "version", "fun_fact")
    list_filter = ("version",)
    search_fields = ("attraction__name", "full_text", "audio_script", "fun_fact")
    autocomplete_fields = ("attraction",)
    list_select_related = ("attraction",)


@admin.register(AudioAsset)
class AudioAssetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "file_name",
        "content",
        "duration_seconds",
        "language",
        "file_link",
    )
    list_filter = ("language",)
    search_fields = ("file_name", "content__attraction__name")
    autocomplete_fields = ("content",)
    list_select_related = ("content", "content__attraction")

    @admin.display(description="音频文件")
    def file_link(self, obj):
        return _external_link(obj.file_url, "打开音频")


@admin.register(LocalVoice)
class LocalVoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "language_label",
        "duration_seconds",
        "display_order",
        "is_active",
        "file_link",
    )
    list_editable = ("display_order", "is_active")
    list_filter = ("language", "is_active")
    search_fields = ("title", "original_file_name")

    @admin.display(description="音频文件")
    def file_link(self, obj):
        return _external_link(obj.file_url, "打开音频")


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "icon", "description")
    search_fields = ("name", "description")


@admin.register(AttractionTheme)
class AttractionThemeAdmin(admin.ModelAdmin):
    list_display = ("id", "attraction", "theme")
    list_filter = ("theme",)
    search_fields = ("attraction__name", "theme__name")
    autocomplete_fields = ("attraction", "theme")
    list_select_related = ("attraction", "theme")


@admin.register(HiddenDetail)
class HiddenDetailAdmin(admin.ModelAdmin):
    list_display = ("id", "attraction", "short_detail", "trigger_distance_meters")
    search_fields = ("attraction__name", "detail_text")
    autocomplete_fields = ("attraction",)
    list_select_related = ("attraction",)

    @admin.display(description="彩蛋文案")
    def short_detail(self, obj):
        return obj.detail_text[:50]


@admin.register(AttractionPath)
class AttractionPathAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "from_attraction",
        "to_attraction",
        "distance_meters",
        "estimated_minutes",
        "is_scenic_route",
    )
    list_filter = ("is_scenic_route",)
    search_fields = ("from_attraction__name", "to_attraction__name")
    autocomplete_fields = ("from_attraction", "to_attraction")
    list_select_related = ("from_attraction", "to_attraction")


@admin.register(Touchpoint)
class TouchpointAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "trigger_code",
        "trigger_type",
        "attraction",
        "physical_location",
    )
    list_filter = ("trigger_type",)
    search_fields = ("trigger_code", "attraction__name", "physical_location")
    autocomplete_fields = ("attraction",)
    list_select_related = ("attraction",)


@admin.register(VisitorSession)
class VisitorSessionAdmin(ReadOnlyEvidenceAdminMixin, admin.ModelAdmin):
    list_display = ("id", "created_at", "last_active_at", "last_known_zone")
    list_filter = ("created_at", "last_active_at", "last_known_zone")
    search_fields = ("=id",)
    autocomplete_fields = ("last_known_zone",)
    list_select_related = ("last_known_zone",)
    readonly_fields = ("id", "created_at", "last_active_at")


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "total_estimated_minutes",
        "generated_at",
        "is_completed",
    )
    list_filter = ("is_completed", "generated_at")
    search_fields = ("=session__id",)
    autocomplete_fields = ("session",)
    list_select_related = ("session",)
    readonly_fields = ("generated_at",)


@admin.register(Footprint)
class FootprintAdmin(ReadOnlyEvidenceAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "itinerary",
        "attraction",
        "touchpoint",
        "triggered_at",
        "audio_played",
    )
    list_filter = ("audio_played", "triggered_at")
    search_fields = ("=session__id", "attraction__name", "touchpoint__trigger_code")
    autocomplete_fields = ("session", "itinerary", "attraction", "touchpoint")
    list_select_related = ("session", "itinerary", "attraction", "touchpoint")
    readonly_fields = ("triggered_at",)


@admin.register(Favorite)
class FavoriteAdmin(ReadOnlyEvidenceAdminMixin, admin.ModelAdmin):
    list_display = ("id", "session", "attraction", "created_at")
    list_filter = ("created_at",)
    search_fields = ("=session__id", "attraction__name")
    autocomplete_fields = ("session", "attraction")
    list_select_related = ("session", "attraction")
    readonly_fields = ("created_at",)


@admin.register(VisitorEvent)
class VisitorEventAdmin(ReadOnlyEvidenceAdminMixin, admin.ModelAdmin):
    list_display = ("id", "session", "event_type", "attraction", "itinerary", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("=session__id", "event_type", "attraction__name")
    autocomplete_fields = ("session", "attraction", "itinerary")
    list_select_related = ("session", "attraction", "itinerary")
    readonly_fields = ("created_at",)
