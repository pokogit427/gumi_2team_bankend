import os

os.environ["DEBUG"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.main import app


LOCATIONS = [
    {
        "id": "1",
        "contentid": "1",
        "title": "금오산",
        "category": "관광지",
        "address": "경상북도 구미시",
        "overview": "등산 명소",
        "latitude": 36.1,
        "longitude": 128.3,
        "image_url": "https://example.com/1.jpg",
        "thumbnail_url": None,
        "telephone": "054-000-0000",
        "content_type_id": 12,
        "source": "테스트 출처",
        "license": "테스트 라이선스",
        "collected_at": "2026-07-15",
        "result_type": "location",
    },
    {
        "id": "2",
        "contentid": "2",
        "title": "구미 식당",
        "category": "음식점",
        "address": "금오산로",
        "overview": "한식 전문점",
        "latitude": 36.2,
        "longitude": 128.4,
        "image_url": None,
        "thumbnail_url": None,
        "telephone": None,
        "content_type_id": 39,
        "source": None,
        "license": None,
        "collected_at": None,
        "result_type": "location",
    },
    {
        "id": "3",
        "contentid": "3",
        "title": "전통 식당",
        "category": "음식점",
        "address": "선산읍",
        "overview": "금오산 근처 음식점",
        "latitude": None,
        "longitude": None,
        "image_url": None,
        "thumbnail_url": None,
        "telephone": None,
        "content_type_id": 39,
        "source": None,
        "license": None,
        "collected_at": None,
        "result_type": "location",
    },
]


@pytest.fixture(autouse=True)
def use_sample_locations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.location_service.get_all_locations",
        lambda: LOCATIONS,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_list_all_locations(client: TestClient) -> None:
    response = client.get("/api/locations")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["page"] == 1
    assert response.json()["size"] == 20


@pytest.mark.parametrize("query, expected_id", [("금오산", "1"), ("구미시", "1"), ("한식", "2")])
def test_searches_title_address_and_overview(
    client: TestClient,
    query: str,
    expected_id: str,
) -> None:
    response = client.get("/api/locations", params={"query": query})

    assert response.status_code == 200
    assert expected_id in [item["id"] for item in response.json()["items"]]


def test_filters_by_category(client: TestClient) -> None:
    response = client.get("/api/locations", params={"category": "음식점"})

    assert response.json()["total"] == 2
    assert {item["category"] for item in response.json()["items"]} == {"음식점"}


def test_combines_query_and_category(client: TestClient) -> None:
    response = client.get(
        "/api/locations",
        params={"query": "근처", "category": "음식점"},
    )

    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == "3"


def test_paginates_locations(client: TestClient) -> None:
    response = client.get("/api/locations", params={"page": 2, "size": 2})

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["page"] == 2
    assert response.json()["size"] == 2
    assert [item["id"] for item in response.json()["items"]] == ["3"]


def test_get_location_detail_includes_metadata(client: TestClient) -> None:
    response = client.get("/api/locations/1")

    assert response.status_code == 200
    assert response.json()["source"] == "테스트 출처"
    assert response.json()["license"] == "테스트 라이선스"
    assert response.json()["collected_at"] == "2026-07-15"


def test_get_missing_location_returns_404(client: TestClient) -> None:
    response = client.get("/api/locations/missing")

    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "message": "Location not found"}


def test_location_with_missing_optional_values_is_valid(client: TestClient) -> None:
    response = client.get("/api/locations/3")

    assert response.status_code == 200
    body = response.json()
    assert body["latitude"] is None
    assert body["longitude"] is None
    assert body["image_url"] is None
    assert body["telephone"] is None
    assert body["source"] is None
