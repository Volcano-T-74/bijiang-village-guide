from collections import Counter
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from main.models import Attraction, Favorite, Footprint, Itinerary, VisitorEvent, VisitorSession


def _counts_by_attraction(queryset):
    return {
        row["attraction_id"]: row["total"]
        for row in queryset.values("attraction_id").annotate(total=Count("id"))
        if row["attraction_id"] is not None
    }


def build_visitor_metrics(days, now=None):
    if not 1 <= days <= 365:
        raise ValueError("days must be between 1 and 365")

    end = now or timezone.now()
    start = end - timedelta(days=days)
    window = {"created_at__gte": start, "created_at__lte": end}
    event_window = VisitorEvent.objects.filter(**window, attraction__isnull=False)
    event_counts = _counts_by_attraction(event_window)
    arrival_counts = _counts_by_attraction(
        event_window.filter(event_type="simulated_arrival")
    )
    footprint_counts = _counts_by_attraction(
        Footprint.objects.filter(triggered_at__gte=start, triggered_at__lte=end)
    )
    favorite_counts = _counts_by_attraction(
        Favorite.objects.filter(created_at__gte=start, created_at__lte=end)
    )
    route_counts = Counter()
    for sequence in Itinerary.objects.filter(
        generated_at__gte=start, generated_at__lte=end
    ).values_list("attraction_sequence", flat=True):
        route_counts.update(set(sequence or ()))

    attractions = []
    for attraction in Attraction.objects.filter(
        status=Attraction.Status.ENABLED
    ).select_related("zone"):
        simulated_arrivals = arrival_counts.get(attraction.id, 0)
        footprints = footprint_counts.get(attraction.id, 0)
        favorites = favorite_counts.get(attraction.id, 0)
        route_appearances = route_counts.get(attraction.id, 0)
        attractions.append(
            {
                "name": attraction.name,
                "slug": attraction.slug,
                "zone": attraction.zone.zone_name,
                "simulated_arrivals": simulated_arrivals,
                "footprints": footprints,
                "favorites": favorites,
                "route_appearances": route_appearances,
                "event_count": event_counts.get(attraction.id, 0),
                "popularity_score": (
                    simulated_arrivals * 4
                    + footprints * 3
                    + favorites * 2
                    + route_appearances
                ),
            }
        )

    attractions.sort(
        key=lambda item: (
            -item["popularity_score"],
            -item["simulated_arrivals"],
            -item["footprints"],
            -item["favorites"],
            -item["route_appearances"],
            item["name"],
        )
    )
    return {
        "period": {
            "days": days,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "total_sessions": VisitorSession.objects.filter(
            created_at__gte=start, created_at__lte=end
        ).count(),
        "score_formula": {
            "simulated_arrival": 4,
            "footprint": 3,
            "favorite": 2,
            "route_appearance": 1,
        },
        "attractions": attractions,
    }
