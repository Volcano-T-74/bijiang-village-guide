from dataclasses import dataclass

from main.models import Attraction, AttractionPath


class NoRouteError(Exception):
    pass


@dataclass(frozen=True)
class Candidate:
    attraction_ids: tuple
    elapsed: int
    score: int
    matched_count: int
    zone_ids: frozenset


def visit_minutes(attraction, mode):
    if mode == "deep":
        return 15 if attraction.depth_level == 2 else 8
    return 10 if attraction.depth_level == 2 else 6


def attraction_score(attraction, preferences, mode, is_new_zone):
    theme_names = {link.theme.name for link in attraction.theme_links.all()}
    matched = sorted(theme_names & preferences)
    score = 1 + len(matched) * 10
    if is_new_zone:
        score += 3
    if mode == "deep" and attraction.depth_level == 2:
        score += 5
    return score, matched


def _candidate_is_better(candidate, best, attractions_by_id):
    if best is None:
        return True
    candidate_key = (
        candidate.score,
        candidate.matched_count,
        len(candidate.zone_ids),
        len(candidate.attraction_ids),
        -candidate.elapsed,
    )
    best_key = (
        best.score,
        best.matched_count,
        len(best.zone_ids),
        len(best.attraction_ids),
        -best.elapsed,
    )
    if candidate_key != best_key:
        return candidate_key > best_key
    candidate_slugs = tuple(
        attractions_by_id[item].slug for item in candidate.attraction_ids
    )
    best_slugs = tuple(attractions_by_id[item].slug for item in best.attraction_ids)
    return candidate_slugs < best_slugs


def _bridge_text(first, second):
    first_themes = {link.theme.name for link in first.theme_links.all()}
    second_themes = {link.theme.name for link in second.theme_links.all()}
    shared = sorted(first_themes & second_themes)
    if first.zone_id == second.zone_id:
        clue = shared[0] if shared else "古村"
        return (
            f"沿着{first.zone.zone_name}继续前行，从“{first.name}”走向"
            f"“{second.name}”，延续“{clue}”线索。"
        )
    source_clue = sorted(first_themes)[0] if first_themes else "古村"
    return (
        f"看完“{first.name}”的“{source_clue}”故事，前往{second.zone.zone_name}；"
        f"{second.zone.visual_cue}，下一站是“{second.name}”。"
    )


def build_route_payload(
    ordered_attractions,
    preferences,
    mode,
    elapsed,
    score,
    paths,
    narrative_bridge=None,
):
    preferences = set(preferences)
    stops = []
    zone_sequence = []
    for attraction in ordered_attractions:
        if attraction.zone_id not in zone_sequence:
            zone_sequence.append(attraction.zone_id)
        _, matched = attraction_score(
            attraction, preferences, mode, attraction.zone_id not in zone_sequence[:-1]
        )
        reasons = []
        if matched:
            reasons.append(f"匹配兴趣：{'、'.join(matched)}")
        if attraction.depth_level == 2:
            reasons.append("深度故事节点")
        if not reasons:
            reasons.append(f"串联{attraction.zone.zone_name}线索")
        stops.append(
            {
                "id": attraction.id,
                "slug": attraction.slug,
                "name": attraction.name,
                "subtitle": attraction.subtitle,
                "zone": {
                    "id": attraction.zone_id,
                    "name": attraction.zone.zone_name,
                    "visual_cue": attraction.zone.visual_cue,
                },
                "depth_level": attraction.depth_level,
                "cover_image_url": attraction.cover_image_url,
                "map_position": {
                    "x": float(attraction.map_x_percent),
                    "y": float(attraction.map_y_percent),
                },
                "themes": sorted(
                    link.theme.name for link in attraction.theme_links.all()
                ),
                "matched_themes": matched,
                "visit_minutes": visit_minutes(attraction, mode),
                "recommendation": "；".join(reasons),
            }
        )

    bridges = {} if narrative_bridge is None else dict(narrative_bridge)
    legs = []
    for first, second in zip(ordered_attractions, ordered_attractions[1:]):
        path = paths.get((first.id, second.id))
        if path is None:
            raise NoRouteError("路线节点之间缺少路径数据。")
        key = f"{first.id}_to_{second.id}"
        bridge = bridges.setdefault(key, _bridge_text(first, second))
        legs.append(
            {
                "from_attraction_id": first.id,
                "to_attraction_id": second.id,
                "from_slug": first.slug,
                "to_slug": second.slug,
                "distance_meters": path.distance_meters,
                "estimated_minutes": path.estimated_minutes,
                "is_scenic_route": path.is_scenic_route,
                "narrative_bridge": bridge,
            }
        )

    return {
        "score": score,
        "total_estimated_minutes": elapsed,
        "zone_sequence": zone_sequence,
        "attraction_sequence": [item.id for item in ordered_attractions],
        "stops": stops,
        "legs": legs,
        "narrative_bridge": bridges,
    }


def generate_route(
    preference_tags,
    duration_minutes,
    mode,
    start_attraction_slug="village-history-museum",
):
    attractions = list(
        Attraction.objects.filter(status=Attraction.Status.ENABLED)
        .select_related("zone")
        .prefetch_related("theme_links__theme")
        .order_by("slug")
    )
    attractions_by_id = {item.id: item for item in attractions}
    try:
        start = next(item for item in attractions if item.slug == start_attraction_slug)
    except StopIteration as exc:
        raise NoRouteError("起点不存在或未启用。") from exc

    paths = {
        (item.from_attraction_id, item.to_attraction_id): item
        for item in AttractionPath.objects.filter(
            from_attraction__in=attractions, to_attraction__in=attractions
        )
    }
    if len(attractions) > 1 and not paths:
        raise NoRouteError("没有可用的景点路径数据。")

    preferences = set(preference_tags)
    start_score, start_matches = attraction_score(start, preferences, mode, True)
    start_elapsed = visit_minutes(start, mode)
    if start_elapsed > duration_minutes:
        raise NoRouteError("时长不足以游览起点。")

    best = None

    def search(route, elapsed, score, matched_count, zone_ids):
        nonlocal best
        candidate = Candidate(
            tuple(item.id for item in route),
            elapsed,
            score,
            matched_count,
            frozenset(zone_ids),
        )
        if _candidate_is_better(candidate, best, attractions_by_id):
            best = candidate

        current = route[-1]
        used_ids = {item.id for item in route}
        for attraction in attractions:
            if attraction.id in used_ids:
                continue
            path = paths.get((current.id, attraction.id))
            if path is None:
                continue
            next_elapsed = (
                elapsed + path.estimated_minutes + visit_minutes(attraction, mode)
            )
            if next_elapsed > duration_minutes:
                continue
            item_score, matched = attraction_score(
                attraction, preferences, mode, attraction.zone_id not in zone_ids
            )
            scenic_bonus = 3 if mode == "relaxed" else 1
            search(
                route + [attraction],
                next_elapsed,
                score + item_score + (scenic_bonus if path.is_scenic_route else 0),
                matched_count + len(matched),
                zone_ids | {attraction.zone_id},
            )

    search(
        [start],
        start_elapsed,
        start_score,
        len(start_matches),
        {start.zone_id},
    )
    if best is None:
        raise NoRouteError("无法在给定约束下生成路线。")
    ordered = [attractions_by_id[item] for item in best.attraction_ids]
    return build_route_payload(
        ordered, preferences, mode, best.elapsed, best.score, paths
    )
