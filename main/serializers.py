from rest_framework import serializers

from main.models import Attraction, Theme


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
