from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Comment, PostLike


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
def client(db_session_factory) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        with db_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_post(client: TestClient) -> int:
    response = client.post(
        "/api/posts",
        json={"title": "추천 장소", "content": "좋은 곳입니다", "password": "post-password"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_comment_is_persisted_without_exposing_password(
    client: TestClient,
    db_session_factory,
) -> None:
    post_id = _create_post(client)

    response = client.post(
        f"/api/posts/{post_id}/comments",
        json={"nickname": "익명 여행자", "content": "저도 추천합니다", "password": "0123"},
    )

    assert response.status_code == 201
    assert response.json()["nickname"] == "익명 여행자"
    assert response.json()["created_at"].endswith("Z")
    assert response.json()["updated_at"].endswith("Z")
    assert "password" not in response.text.casefold()
    with db_session_factory() as db:
        saved = db.get(Comment, response.json()["id"])
        assert saved is not None
        assert saved.password_hash != "0123"


@pytest.mark.parametrize("password", ["123", "12345", "12a4", "１２３４", "    "])
def test_comment_requires_four_ascii_digits(client: TestClient, password: str) -> None:
    post_id = _create_post(client)

    response = client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": "댓글", "password": password},
    )

    assert response.status_code == 422


def test_comments_are_listed_oldest_first(client: TestClient) -> None:
    post_id = _create_post(client)
    first = client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": "첫 댓글", "password": "1111"},
    ).json()
    second = client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": "둘째 댓글", "password": "2222"},
    ).json()

    response = client.get(f"/api/posts/{post_id}/comments")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [item["id"] for item in response.json()["items"]] == [first["id"], second["id"]]


def test_comments_support_pagination(client: TestClient) -> None:
    post_id = _create_post(client)
    for index in range(3):
        client.post(
            f"/api/posts/{post_id}/comments",
            json={"content": f"댓글 {index}", "password": "1234"},
        )

    response = client.get(
        f"/api/posts/{post_id}/comments",
        params={"page": 2, "size": 2},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["page"] == 2
    assert response.json()["size"] == 2
    assert [item["content"] for item in response.json()["items"]] == ["댓글 2"]


def test_comment_deletion_requires_its_password(client: TestClient) -> None:
    post_id = _create_post(client)
    comment_id = client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": "삭제할 댓글", "password": "1234"},
    ).json()["id"]

    rejected = client.request(
        "DELETE",
        f"/api/posts/{post_id}/comments/{comment_id}",
        json={"password": "9999"},
    )
    deleted = client.request(
        "DELETE",
        f"/api/posts/{post_id}/comments/{comment_id}",
        json={"password": "1234"},
    )

    assert rejected.status_code == 403
    assert rejected.json()["code"] == "invalid_password"
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/api/posts/{post_id}/comments").json()["total"] == 0


def test_likes_accumulate_and_counts_are_returned_with_post(client: TestClient) -> None:
    post_id = _create_post(client)

    first = client.post(f"/api/posts/{post_id}/like")
    second = client.post(f"/api/posts/{post_id}/like")
    detail = client.get(f"/api/posts/{post_id}")

    assert first.json()["likes"] == 1
    assert second.json()["likes"] == 2
    assert detail.json()["likes"] == 2
    assert detail.json()["like_count"] == 2
    assert detail.json()["comment_count"] == 0


def test_post_response_uses_frontend_fields_and_tracks_comment_count(client: TestClient) -> None:
    post_id = _create_post(client)
    client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": "집계할 댓글", "password": "1234"},
    )

    first = client.get(f"/api/posts/{post_id}").json()
    second = client.get(f"/api/posts/{post_id}").json()

    assert first["views"] == 1
    assert second["views"] == 2
    assert second["comment_count"] == 1
    assert second["created_at"].endswith("Z")


def test_deleting_post_also_deletes_comments_and_likes(
    client: TestClient,
    db_session_factory,
) -> None:
    post_id = _create_post(client)
    client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": "함께 삭제", "password": "1234"},
    )
    client.post(f"/api/posts/{post_id}/likes")

    response = client.request(
        "DELETE",
        f"/api/posts/{post_id}",
        json={"password": "post-password"},
    )

    assert response.status_code == 200
    with db_session_factory() as db:
        comment_count = db.scalar(select(func.count()).select_from(Comment))
        like_count = db.scalar(select(func.count()).select_from(PostLike))
        assert comment_count == 0
        assert like_count == 0


def test_missing_post_returns_404_for_comments_and_likes(client: TestClient) -> None:
    comment = client.post(
        "/api/posts/999/comments",
        json={"content": "댓글", "password": "1234"},
    )
    like = client.post("/api/posts/999/like")

    assert comment.status_code == 404
    assert like.status_code == 404
