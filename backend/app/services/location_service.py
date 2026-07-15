"""Load and normalize location data from the project's JSON files."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger("localhub.location_service")
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

CATEGORY_BY_CONTENT_TYPE_ID = {
    "12": "관광지",
    "14": "문화시설",
    "15": "축제공연행사",
    "25": "여행코스",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
    "39": "음식점",
}


class LocationDataError(RuntimeError):
    """Raised when the location data set cannot be loaded safely."""


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coordinate(value: object, *, field: str, content_id: str) -> float | None:
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        logger.warning("Invalid %s for location contentid=%s; using None", field, content_id)
        return None


def normalize_location(
    item: Mapping[str, Any],
    *,
    file_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert one source item into the shape consumed by API schemas."""
    metadata = file_metadata or {}
    content_id = str(item.get("contentid", "")).strip()
    content_type_id = str(item.get("contenttypeid", "")).strip()
    address_parts = filter(None, (_optional_text(item.get("addr1")), _optional_text(item.get("addr2"))))

    return {
        "id": content_id,
        "contentid": content_id,
        "title": item.get("title", ""),
        "overview": item.get("overview"),
        "category": CATEGORY_BY_CONTENT_TYPE_ID.get(
            content_type_id,
            _optional_text(metadata.get("contentType")) or "기타",
        ),
        "content_type_id": int(content_type_id) if content_type_id.isdigit() else None,
        "address": " ".join(address_parts) or None,
        "latitude": _coordinate(item.get("mapy"), field="mapy", content_id=content_id),
        "longitude": _coordinate(item.get("mapx"), field="mapx", content_id=content_id),
        "image_url": _optional_text(item.get("firstimage"))
        or _optional_text(item.get("firstimage2")),
        "thumbnail_url": _optional_text(item.get("firstimage2")),
        "telephone": _optional_text(item.get("tel")),
        "source": _optional_text(metadata.get("source")),
        "license": _optional_text(metadata.get("license")),
        "collected_at": _optional_text(metadata.get("collected_at")),
        "result_type": "location",
    }


@lru_cache(maxsize=None)
def _load_locations_cached(data_directory: str) -> tuple[dict[str, Any], ...]:
    data_path = Path(data_directory)
    json_files = sorted(data_path.glob("*.json")) if data_path.is_dir() else []
    if not json_files:
        message = f"No location JSON files found in data directory: {data_path}"
        logger.error(message)
        raise LocationDataError(message)

    locations_by_id: dict[str, dict[str, Any]] = {}
    for json_file in json_files:
        try:
            with json_file.open(encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            message = f"Failed to load location JSON file '{json_file}': {exc}"
            logger.error(message)
            raise LocationDataError(message) from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            message = f"Location JSON file '{json_file}' must contain an 'items' array"
            logger.error(message)
            raise LocationDataError(message)

        for item in payload["items"]:
            if not isinstance(item, dict):
                logger.warning("Skipping non-object item in location file '%s'", json_file)
                continue
            normalized = normalize_location(item, file_metadata=payload)
            content_id = normalized["contentid"]
            if not content_id:
                logger.warning("Skipping location without contentid in file '%s'", json_file)
                continue
            locations_by_id.setdefault(content_id, normalized)

    logger.info(
        "Loaded %d unique locations from %d JSON files",
        len(locations_by_id),
        len(json_files),
    )
    return tuple(locations_by_id.values())


def load_locations(data_directory: str | Path | None = None) -> list[dict[str, Any]]:
    """Load all JSON files once per data directory and return normalized locations."""
    directory = Path(data_directory or DEFAULT_DATA_DIR).resolve()
    return list(_load_locations_cached(str(directory)))


def get_all_locations() -> list[dict[str, Any]]:
    return load_locations()


def get_location_by_content_id(content_id: str | int) -> dict[str, Any] | None:
    target = str(content_id).strip()
    return next((item for item in get_all_locations() if item["contentid"] == target), None)


def filter_locations(
    query: str | None = None,
    category: str | None = None,
    *,
    locations: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Filter cached locations by category and title/address/overview text."""
    candidates = get_all_locations() if locations is None else locations
    query_text = query.strip().casefold() if query else ""
    category_text = category.strip().casefold() if category else ""

    return [
        item
        for item in candidates
        if (not category_text or str(item.get("category", "")).casefold() == category_text)
        and (
            not query_text
            or any(
                query_text in str(item.get(field) or "").casefold()
                for field in ("title", "address", "overview")
            )
        )
    ]


def get_location_page(
    *,
    query: str | None = None,
    category: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Return a filtered page and the total number of matching locations."""
    filtered = filter_locations(query=query, category=category)
    start = (page - 1) * size
    return filtered[start : start + size], len(filtered)


def clear_location_cache() -> None:
    """Clear the loader cache, primarily for tests and explicit data refreshes."""
    _load_locations_cached.cache_clear()
