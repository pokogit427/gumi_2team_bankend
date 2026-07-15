"""Combine location and community post search results."""

from typing import Any, Literal

from sqlalchemy.orm import Session

from app.services.location_service import filter_locations
from app.services.post_service import search_posts

SearchCategory = Literal["all", "tourist", "restaurant", "festival", "community"]

LOCATION_CATEGORY_NAMES = {
    "tourist": "관광지",
    "restaurant": "음식점",
    "festival": "축제공연행사",
}


def _location_result(location: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": location["id"],
        "title": location["title"],
        "summary": location.get("overview") or location.get("address") or "",
        "category": location["category"],
        "source": location.get("source"),
        "license": location.get("license"),
        "collected_at": location.get("collected_at"),
        "result_type": "location",
    }


def _post_result(post: Any) -> dict[str, Any]:
    return {
        "id": post.id,
        "title": post.title,
        "summary": post.content,
        "category": "community",
        "source": "community",
        "license": None,
        "collected_at": None,
        "result_type": "post",
    }


def search_all(
    db: Session,
    *,
    query: str,
    category: SearchCategory,
    page: int,
    size: int,
) -> tuple[list[dict[str, Any]], int]:
    """Search selected data sources, combine results, and apply pagination."""
    query_text = query.strip()
    results: list[dict[str, Any]] = []

    if category != "community":
        location_category = LOCATION_CATEGORY_NAMES.get(category)
        locations = filter_locations(query=query_text, category=location_category)
        results.extend(_location_result(location) for location in locations)

    if category in ("all", "community"):
        posts = search_posts(db, query_text)
        results.extend(_post_result(post) for post in posts)

    start = (page - 1) * size
    return results[start : start + size], len(results)
