import os

os.environ["DEBUG"] = "false"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


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
def client(db_session_factory, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    # 테스트용 DB 세션 오버라이드
    def override_get_db() -> Generator[Session, None, None]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_chat_tourist_question_returns_locations(monkeypatch, client: TestClient):
    # 모킹된 위치 결과
    monkeypatch.setattr(
        "app.services.location_service.filter_locations",
        lambda query, category, locations=None: [
            {"id": "1", "title": "금오산"},
            {"id": "2", "title": "구미박물관"},
        ],
    )

    response = client.post("/api/chat", json={"message": "구미 관광 추천"})

    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert isinstance(body["references"], list)
    assert len(body["references"]) >= 1


def test_chat_restaurant_question_returns_restaurants(monkeypatch, client: TestClient):
    monkeypatch.setattr(
        "app.services.location_service.filter_locations",
        lambda query, category, locations=None: [{"id": "r1", "title": "맛집A"}],
    )

    response = client.post("/api/chat", json={"message": "맛집 추천"})

    assert response.status_code == 200
    assert "맛집A" in response.json()["answer"]


def test_chat_post_question_searches_posts(monkeypatch, client: TestClient):
    # 게시글 검색은 DB 세션을 이용하므로 ORM 객체처럼 최소한의 속성 제공
    class FakePost:
        def __init__(self, id, title):
            self.id = id
            self.title = title

    monkeypatch.setattr(
        "app.services.post_service.search_posts",
        lambda db, query: [FakePost(1, "게시글A"), FakePost(2, "게시글B")],
    )

    response = client.post("/api/chat", json={"message": "게시글 검색"})

    assert response.status_code == 200
    body = response.json()
    assert any(r["result_type"] == "post" for r in body["references"]) or "관련 게시글" in body["answer"]


def test_chat_empty_message_rejected(client: TestClient):
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 422


def test_chat_service_internal_error(monkeypatch, client: TestClient):
    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.services.chat_service.filter_locations", fail)

    response = client.post("/api/chat", json={"message": "구미 관광"})
    assert response.status_code == 500
    assert response.json() == {"error": "server_error", "message": "Internal server error"}
