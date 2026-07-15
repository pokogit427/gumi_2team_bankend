import json
from pathlib import Path

import pytest

from app.services.location_service import (
    LocationDataError,
    clear_location_cache,
    get_location_by_content_id,
    load_locations,
    normalize_location,
)


@pytest.fixture(autouse=True)
def reset_location_cache() -> None:
    clear_location_cache()
    yield
    clear_location_cache()


def _write_data(path: Path, name: str, items: list[dict[str, object]], **metadata: object) -> None:
    payload = {"contentType": "관광지", "items": items, **metadata}
    (path / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_loads_all_json_files_and_removes_duplicate_content_ids(tmp_path: Path) -> None:
    _write_data(
        tmp_path,
        "first.json",
        [{"contentid": 1, "contenttypeid": "12", "title": "첫 장소"}],
    )
    _write_data(
        tmp_path,
        "second.json",
        [
            {"contentid": "1", "contenttypeid": "39", "title": "중복 장소"},
            {"contentid": "2", "contenttypeid": "39", "title": "둘째 장소"},
        ],
        contentType="음식점",
    )

    locations = load_locations(tmp_path)

    assert [item["contentid"] for item in locations] == ["1", "2"]
    assert locations[0]["title"] == "첫 장소"


def test_normalizes_empty_coordinates_category_and_optional_fields() -> None:
    location = normalize_location(
        {
            "contentid": 3032819,
            "contenttypeid": "12",
            "title": " 원본 제목 ",
            "overview": " 원본 설명 ",
            "mapx": "",
            "mapy": None,
        },
        file_metadata={"source": "공공데이터", "license": "테스트 라이선스", "collected_at": "2026-07-15"},
    )

    assert location["contentid"] == "3032819"
    assert location["category"] == "관광지"
    assert location["longitude"] is None
    assert location["latitude"] is None
    assert location["title"] == " 원본 제목 "
    assert location["overview"] == " 원본 설명 "
    assert location["address"] is None
    assert location["image_url"] is None
    assert location["telephone"] is None
    assert location["source"] == "공공데이터"


def test_get_location_by_content_id_uses_cached_default_data(monkeypatch: pytest.MonkeyPatch) -> None:
    cached = [{"contentid": "3032819", "title": "검성지 생태공원"}]
    monkeypatch.setattr("app.services.location_service.get_all_locations", lambda: cached)

    assert get_location_by_content_id(3032819) == cached[0]
    assert get_location_by_content_id("missing") is None


def test_invalid_json_raises_clear_error(tmp_path: Path) -> None:
    broken_file = tmp_path / "broken.json"
    broken_file.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(LocationDataError, match=r"broken\.json"):
        load_locations(tmp_path)


def test_missing_json_raises_clear_error(tmp_path: Path) -> None:
    with pytest.raises(LocationDataError, match="No location JSON files"):
        load_locations(tmp_path)
