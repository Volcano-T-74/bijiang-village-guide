from rest_framework import serializers

from main.models import Attraction, Theme, Touchpoint


class SessionCreateSerializer(serializers.Serializer):
    preference_tags = serializers.ListField(
        child=serializers.CharField(max_length=20), required=False, default=list
    )

    def validate_preference_tags(self, value):
        valid = set(Theme.objects.filter(name__in=value).values_list("name", flat=True))
        invalid = sorted(set(value) - valid)
        if invalid:
            raise serializers.ValidationError(f"无效主题：{'、'.join(invalid)}")
        return list(dict.fromkeys(value))


class ItineraryGenerateSerializer(serializers.Serializer):
    preference_tags = serializers.ListField(
        child=serializers.CharField(max_length=20), allow_empty=True
    )
    duration_minutes = serializers.ChoiceField(choices=(30, 60, 90))
    mode = serializers.ChoiceField(choices=("relaxed", "deep"))
    start_attraction_slug = serializers.SlugField(
        required=False, default="village-history-museum"
    )

    def validate_preference_tags(self, value):
        valid = set(Theme.objects.filter(name__in=value).values_list("name", flat=True))
        invalid = sorted(set(value) - valid)
        if invalid:
            raise serializers.ValidationError(f"无效主题：{'、'.join(invalid)}")
        return list(dict.fromkeys(value))

    def validate_start_attraction_slug(self, value):
        exists = Attraction.objects.filter(
            slug=value, status=Attraction.Status.ENABLED
        ).exists()
        if not exists:
            raise serializers.ValidationError("起点不存在或未启用。")
        return value


class AttractionSlugSerializer(serializers.Serializer):
    attraction_slug = serializers.SlugField()

    def validate_attraction_slug(self, value):
        try:
            self.attraction = Attraction.objects.get(
                slug=value, status=Attraction.Status.ENABLED
            )
        except Attraction.DoesNotExist as exc:
            raise serializers.ValidationError("景点不存在或未启用。") from exc
        return value


class EventCreateSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=50)
    attraction_slug = serializers.SlugField(required=False)
    itinerary_id = serializers.IntegerField(required=False)
    metadata = serializers.JSONField(required=False, default=dict)

    def validate_attraction_slug(self, value):
        try:
            self.attraction = Attraction.objects.get(
                slug=value, status=Attraction.Status.ENABLED
            )
        except Attraction.DoesNotExist as exc:
            raise serializers.ValidationError("景点不存在或未启用。") from exc
        return value


class FavoriteCreateSerializer(AttractionSlugSerializer):
    pass


class FootprintCreateSerializer(AttractionSlugSerializer):
    itinerary_id = serializers.IntegerField()
    touchpoint_code = serializers.CharField(max_length=20, required=False)
    audio_played = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get("touchpoint_code"):
            try:
                self.touchpoint = Touchpoint.objects.get(
                    trigger_code=attrs["touchpoint_code"],
                    attraction=self.attraction,
                )
            except Touchpoint.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {"touchpoint_code": "触点不存在或不属于该景点。"}
                ) from exc
        else:
            self.touchpoint = Touchpoint.objects.filter(attraction=self.attraction).first()
            if self.touchpoint is None:
                self.touchpoint, _ = Touchpoint.objects.get_or_create(
                    trigger_code=f"sim-{self.attraction.id}",
                    defaults={
                        "attraction": self.attraction,
                        "trigger_type": Touchpoint.TriggerType.SIMULATE,
                        "physical_location": "前端模拟打卡",
                    },
                )
        return attrs
