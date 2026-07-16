import os
from collections.abc import Generator

os.environ["DEBUG"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Post
from app.services.post_service import PostCreationError


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
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_post_returns_201_without_password_and_persists(
    client: TestClient,
    db_session_factory,
) -> None:
    response = client.post(
        "/api/posts",
        json={"title": "구미 여행 후기", "content": "좋았어요", "password": "1234"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "구미 여행 후기"
    assert body["content"] == "좋았어요"
    assert "password" not in body

    with db_session_factory() as db:
        saved_post = db.scalar(select(Post).where(Post.id == body["id"]))
        assert saved_post is not None
        assert saved_post.title == "구미 여행 후기"
        assert saved_post.content == "좋았어요"
        assert saved_post.password == "1234"


@pytest.mark.parametrize("field", ["title", "content", "password"])
def test_create_post_rejects_blank_required_values(client: TestClient, field: str) -> None:
    payload = {"title": "제목", "content": "내용", "password": "1234"}
    payload[field] = "   "

    response = client.post("/api/posts", json=payload)

    assert response.status_code == 422


def test_create_post_hides_database_error_details(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_to_create(*args, **kwargs):
        raise PostCreationError("sensitive database detail")

    monkeypatch.setattr("app.routers.posts.create_post", fail_to_create)

    response = client.post(
        "/api/posts",
        json={"title": "제목", "content": "내용", "password": "secret"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "code": "server_error",
        "message": "Internal server error",
    }
    assert "sensitive" not in response.text
    assert "secret" not in response.text


def _create_posts(client: TestClient, count: int) -> list[dict]:
    return [
        client.post(
            "/api/posts",
            json={"title": f"제목 {index}", "content": f"내용 {index}", "password": "1234"},
        ).json()
        for index in range(count)
    ]


def test_list_posts_returns_empty_page(client: TestClient) -> None:
    response = client.get("/api/posts")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 20}


def test_list_posts_returns_newest_first_without_password(client: TestClient) -> None:
    created = _create_posts(client, 3)

    response = client.get("/api/posts")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert [item["id"] for item in body["items"]] == [
        created[2]["id"],
        created[1]["id"],
        created[0]["id"],
    ]
    assert all("password" not in item for item in body["items"])


def test_list_posts_supports_pagination(client: TestClient) -> None:
    created = _create_posts(client, 5)

    response = client.get("/api/posts?page=2&size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert body["page"] == 2
    assert body["size"] == 2
    assert [item["id"] for item in body["items"]] == [created[2]["id"], created[1]["id"]]


def test_get_post_returns_detail_without_password_and_increments_view_count(
    client: TestClient,
    db_session_factory,
) -> None:
    post_id = _create_posts(client, 1)[0]["id"]

    first_response = client.get(f"/api/posts/{post_id}")
    second_response = client.get(f"/api/posts/{post_id}")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == post_id
    assert "password" not in first_response.json()
    with db_session_factory() as db:
        saved_post = db.get(Post, post_id)
        assert saved_post is not None
        assert saved_post.view_count == 2


def test_get_missing_post_returns_404(client: TestClient) -> None:
    response = client.get("/api/posts/999999")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "Post not found"}


def test_update_post_changes_content_and_updated_at_without_exposing_password(
    client: TestClient,
    db_session_factory,
) -> None:
    created = _create_posts(client, 1)[0]
    original_updated_at = created["updated_at"]

    response = client.put(
        f"/api/posts/{created['id']}",
        json={"title": "수정된 제목", "content": "수정된 내용", "password": "1234"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "수정된 제목"
    assert body["content"] == "수정된 내용"
    assert body["updated_at"] != original_updated_at
    assert "password" not in body
    with db_session_factory() as db:
        saved_post = db.get(Post, created["id"])
        assert saved_post is not None
        assert saved_post.title == "수정된 제목"
        assert saved_post.content == "수정된 내용"
        assert saved_post.password == "1234"


def test_update_post_rejects_incorrect_password(client: TestClient) -> None:
    created = _create_posts(client, 1)[0]

    response = client.put(
        f"/api/posts/{created['id']}",
        json={"title": "수정 시도", "content": "수정 시도", "password": "wrong"},
    )

    assert response.status_code == 403
    assert response.json() == {"code": "forbidden", "message": "Incorrect password"}


def test_update_missing_post_returns_404(client: TestClient) -> None:
    response = client.put(
        "/api/posts/999999",
        json={"title": "제목", "content": "내용", "password": "1234"},
    )

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "Post not found"}


@pytest.mark.parametrize("field", ["title", "content"])
def test_update_post_rejects_blank_text(client: TestClient, field: str) -> None:
    created = _create_posts(client, 1)[0]
    payload = {"title": "수정 제목", "content": "수정 내용", "password": "1234"}
    payload[field] = "   "

    response = client.put(f"/api/posts/{created['id']}", json=payload)

    assert response.status_code == 422


def test_delete_post_removes_post_and_does_not_expose_password(client: TestClient) -> None:
    created = _create_posts(client, 1)[0]

    response = client.request(
        "DELETE",
        f"/api/posts/{created['id']}",
        json={"password": "1234"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Post deleted"}
    assert "password" not in response.text.casefold()
    assert "1234" not in response.text


def test_delete_post_rejects_incorrect_password(client: TestClient) -> None:
    created = _create_posts(client, 1)[0]

    response = client.request(
        "DELETE",
        f"/api/posts/{created['id']}",
        json={"password": "wrong"},
    )

    assert response.status_code == 403
    assert response.json() == {"code": "forbidden", "message": "Incorrect password"}
    assert client.get(f"/api/posts/{created['id']}").status_code == 200


def test_delete_missing_post_returns_404(client: TestClient) -> None:
    response = client.request(
        "DELETE",
        "/api/posts/999999",
        json={"password": "1234"},
    )

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "Post not found"}


@pytest.mark.parametrize("password", ["", "   "])
def test_delete_post_rejects_empty_or_blank_password(
    client: TestClient,
    password: str,
) -> None:
    created = _create_posts(client, 1)[0]

    response = client.request(
        "DELETE",
        f"/api/posts/{created['id']}",
        json={"password": password},
    )

    assert response.status_code == 422


def test_get_post_returns_404_after_delete(client: TestClient) -> None:
    created = _create_posts(client, 1)[0]
    client.request(
        "DELETE",
        f"/api/posts/{created['id']}",
        json={"password": "1234"},
    )

    response = client.get(f"/api/posts/{created['id']}")

    assert response.status_code == 404
