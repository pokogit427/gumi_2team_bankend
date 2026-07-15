"""Business logic for community posts."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Post
from app.schemas import PostCreate, PostDeleteRequest, PostUpdate

logger = logging.getLogger("localhub.post_service")


class PostCreationError(RuntimeError):
    """Raised when a post cannot be persisted."""


class PostReadError(RuntimeError):
    """Raised when posts cannot be read or updated safely."""


class PostNotFoundError(LookupError):
    """Raised when the requested post does not exist."""


class IncorrectPostPasswordError(PermissionError):
    """Raised when a post password does not match."""


def create_post(db: Session, post_data: PostCreate) -> Post:
    """Persist a new post and return the refreshed ORM object."""
    post = Post(
        title=post_data.title,
        content=post_data.content,
        password=post_data.password,
    )

    try:
        db.add(post)
        db.commit()
        db.refresh(post)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to create post due to a database error")
        raise PostCreationError("Post could not be created") from exc

    return post


def get_posts(db: Session, *, page: int, size: int) -> tuple[list[Post], int]:
    """Return one page of posts ordered from newest to oldest."""
    try:
        total = db.scalar(select(func.count()).select_from(Post)) or 0
        posts = list(
            db.scalars(
                select(Post)
                .order_by(Post.created_at.desc(), Post.id.desc())
                .offset((page - 1) * size)
                .limit(size)
            ).all()
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to read posts due to a database error")
        raise PostReadError("Posts could not be read") from exc

    return posts, total


def search_posts(db: Session, query: str) -> list[Post]:
    """Search post titles and content, newest first."""
    query_text = query.strip()
    try:
        return list(
            db.scalars(
                select(Post)
                .where(Post.title.ilike(f"%{query_text}%") | Post.content.ilike(f"%{query_text}%"))
                .order_by(Post.created_at.desc(), Post.id.desc())
            ).all()
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to search posts due to a database error")
        raise PostReadError("Posts could not be searched") from exc


def get_post_and_increment_view_count(db: Session, post_id: int) -> Post:
    """Return a post after atomically incrementing its view count."""
    try:
        post = db.get(Post, post_id)
        if post is None:
            raise PostNotFoundError("Post not found")

        post.view_count += 1
        db.commit()
        db.refresh(post)
        return post
    except PostNotFoundError:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to read a post due to a database error")
        raise PostReadError("Post could not be read") from exc


def update_post(db: Session, post_id: int, post_data: PostUpdate) -> Post:
    """Update a post after validating its existing password."""
    try:
        post = db.get(Post, post_id)
        if post is None:
            raise PostNotFoundError("Post not found")

        # 교육용 과제 요구사항에 따라 저장된 평문 비밀번호를 직접 비교한다.
        if post.password != post_data.password:
            raise IncorrectPostPasswordError("Incorrect password")

        post.title = post_data.title
        post.content = post_data.content
        post.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(post)
        return post
    except (PostNotFoundError, IncorrectPostPasswordError):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to update a post due to a database error")
        raise PostReadError("Post could not be updated") from exc


def delete_post(db: Session, post_id: int, delete_data: PostDeleteRequest) -> None:
    """Delete a post after validating its existing password."""
    try:
        post = db.get(Post, post_id)
        if post is None:
            raise PostNotFoundError("Post not found")

        # 교육용 과제 요구사항에 따라 저장된 평문 비밀번호를 직접 비교한다.
        if post.password != delete_data.password:
            raise IncorrectPostPasswordError("Incorrect password")

        db.delete(post)
        db.commit()
    except (PostNotFoundError, IncorrectPostPasswordError):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to delete a post due to a database error")
        raise PostReadError("Post could not be deleted") from exc
