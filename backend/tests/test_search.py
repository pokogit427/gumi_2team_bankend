import os
from collections.abc import Generator

os.environ["DEBUG"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


LOCATIONS = [
    {
        "id": "loc-1",
        "title": "Common 공통 금오산",
        "overview": "관광지 설명",
        "address": "구미시",
        "category": "관광지",
        "source": "공공데이터",
        "license": "공공누리",
        "collected_at": "2026-07-15",
    },
    {
        "id": "loc-2",
        "title": "맛집 전용어",
        "overview": "음식점 설명",
        "address": "구미시",
        "category": "음식점",
        "source": None,
        "license": None,
        "collected_at": None,
    },
    {
        "id": "loc-3",
        "title": "축제 전용어",
        "overview": "행사 설명",
        "address": "구미시",
        "category": "축제공연행사",
        "source": None,
        "license": None,
        "collected_at": None,
    },
]


@pytest.fixture
def db_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(
    db_session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        with db_session_factory() as db:
            yield db

    monkeypatch.setattr("app.services.location_service.get_all_locations", lambda: LOCATIONS)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.post(
            "/api/posts",
            json={"title": "common 공통 게시글", "content": "게시글 전용어", "password": "secret"},
        )
        yield test_client
    app.dependency_overrides.clear()


def test_searches_location_only(client: TestClient) -> None:
    response = client.get("/api/search", params={"query": "금오산"})

    assert response.status_code == 200
    assert [item["result_type"] for item in response.json()["items"]] == ["location"]


def test_searches_post_only_without_password(client: TestClient) -> None:
    response = client.get("/api/search", params={"query": "게시글 전용어"})

    assert response.status_code == 200
    assert [item["result_type"] for item in response.json()["items"]] == ["post"]
    assert "password" not in response.text.casefold()
    assert "secret" not in response.text


def test_searches_both_sources_case_insensitively(client: TestClient) -> None:
    response = client.get("/api/search", params={"query": "  COMMON  "})

    assert response.status_code == 200
    assert {item["result_type"] for item in response.json()["items"]} == {"location", "post"}


def test_community_filter_returns_posts_only(client: TestClient) -> None:
    response = client.get(
        "/api/search",
        params={"query": "공통", "category": "community"},
    )

    assert response.json()["total"] == 1
    assert response.json()["items"][0]["result_type"] == "post"


@pytest.mark.parametrize(
    "category, query, expected_category",
    [
        ("tourist", "공통", "관광지"),
        ("restaurant", "전용어", "음식점"),
        ("festival", "전용어", "축제공연행사"),
    ],
)
def test_location_category_filters(
    client: TestClient,
    category: str,
    query: str,
    expected_category: str,
) -> None:
    response = client.get(
        "/api/search",
        params={"query": query, "category": category},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["category"] == expected_category


def test_returns_empty_result(client: TestClient) -> None:
    response = client.get("/api/search", params={"query": "검색결과없음"})

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 20}


@pytest.mark.parametrize("query", ["", "   "])
def test_rejects_empty_query(client: TestClient, query: str) -> None:
    response = client.get("/api/search", params={"query": query})

    assert response.status_code == 422


def test_paginates_combined_results(client: TestClient) -> None:
    response = client.get(
        "/api/search",
        params={"query": "공통", "page": 2, "size": 1},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 2
    assert len(response.json()["items"]) == 1
