import math
from urllib.parse import quote

from django.core.management.base import BaseCommand
from django.db import transaction

from main.demo_data import ATTRACTIONS, THEMES, ZONES
from main.models import (
    Attraction,
    AttractionPath,
    AttractionTheme,
    StoryContent,
    Theme,
    Zone,
)


def build_audio_script(full_text):
    paragraphs = [part.strip() for part in full_text.split("\n\n") if part.strip()]
    if len(paragraphs) <= 1:
        return paragraphs[0] if paragraphs else ""
    return f"{paragraphs[0]}\n\n{paragraphs[-1]}"


def demo_distance(first, second):
    raw_distance = math.hypot(
        float(first.map_x_percent - second.map_x_percent),
        float(first.map_y_percent - second.map_y_percent),
    ) * 7
    return max(80, int(raw_distance / 10 + 0.5) * 10)


class Command(BaseCommand):
    help = "Create or update the canonical nine-attraction Bijiang demo dataset."

    @transaction.atomic
    def handle(self, *args, **options):
        zones = {}
        for name, values in ZONES.items():
            zones[name], _ = Zone.objects.update_or_create(
                zone_name=name,
                defaults={
                    "center_latitude": None,
                    "center_longitude": None,
                    **values,
                },
            )

        themes = {}
        for name, (icon, description) in THEMES.items():
            themes[name], _ = Theme.objects.update_or_create(
                name=name, defaults={"icon": icon, "description": description}
            )

        attractions = []
        for order, item in enumerate(ATTRACTIONS, start=1):
            attraction, _ = Attraction.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "zone": zones[item["zone"]],
                    "name": item["name"],
                    "subtitle": item["subtitle"],
                    "type": item["type"],
                    "depth_level": item["depth_level"],
                    "cover_image_url": f"/static/{quote(item['cover'])}",
                    "latitude": None,
                    "longitude": None,
                    "map_x_percent": item["map"][0],
                    "map_y_percent": item["map"][1],
                    "display_order": order,
                    "status": Attraction.Status.ENABLED,
                },
            )
            attractions.append(attraction)
            StoryContent.objects.update_or_create(
                attraction=attraction,
                version=1,
                defaults={
                    "full_text": item["story"].strip(),
                    "audio_script": build_audio_script(item["story"]),
                    "fun_fact": item["fun_fact"],
                },
            )
            for theme_name in item["themes"]:
                AttractionTheme.objects.get_or_create(
                    attraction=attraction, theme=themes[theme_name]
                )

        west_slugs = {
            "village-history-museum",
            "huang-ancestral-hall",
            "poetry-lane",
            "xiuxi-peng-ancestral-hall",
        }
        east_slugs = {
            "bixi-scholar-hall",
            "dong-ancestral-hall",
            "old-wharf",
            "waterside-ancient-tree",
        }
        bridge_slug = "ancient-bridge"
        allowed_pairs = {
            (first.slug, second.slug)
            for bank in (west_slugs, east_slugs)
            for first in attractions
            for second in attractions
            if first.slug in bank and second.slug in bank and first.pk != second.pk
        }
        allowed_pairs.update(
            {
                pair
                for slug in west_slugs | east_slugs
                for pair in ((slug, bridge_slug), (bridge_slug, slug))
            }
        )
        attractions_by_slug = {item.slug: item for item in attractions}
        AttractionPath.objects.filter(
            from_attraction__in=attractions,
            to_attraction__in=attractions,
        ).delete()

        scenic_slugs = {bridge_slug, "old-wharf", "waterside-ancient-tree"}
        for first_slug, second_slug in sorted(allowed_pairs):
                first = attractions_by_slug[first_slug]
                second = attractions_by_slug[second_slug]
                distance = demo_distance(first, second)
                AttractionPath.objects.update_or_create(
                    from_attraction=first,
                    to_attraction=second,
                    defaults={
                        "distance_meters": distance,
                        "estimated_minutes": math.ceil(distance / 75),
                        "is_scenic_route": (
                            first.slug in scenic_slugs and second.slug in scenic_slugs
                        ),
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data ready: 4 zones, 9 attractions, 6 themes, 9 stories, 40 paths."
            )
        )
