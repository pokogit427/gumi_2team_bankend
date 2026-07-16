"""Business logic for anonymous post comments and likes."""

import hashlib
import hmac
import logging
import secrets

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Comment, Post, PostLike
from app.schemas import CommentCreate

logger = logging.getLogger("localhub.comment_service")


class CommentServiceError(RuntimeError):
    """Raised when comment or like persistence fails."""


class ParentPostNotFoundError(LookupError):
    """Raised when the parent post does not exist."""


class CommentNotFoundError(LookupError):
    """Raised when a comment does not exist under the requested post."""


class IncorrectCommentPasswordError(PermissionError):
    """Raised when a comment deletion password does not match."""


def _hash_password(password: str, *, salt: bytes | None = None) -> str:
    actual_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), actual_salt, 210_000)
    return f"pbkdf2_sha256${actual_salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_hex, expected_hex = encoded.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = _hash_password(password, salt=bytes.fromhex(salt_hex)).rsplit("$", 1)[1]
        return hmac.compare_digest(actual, expected_hex)
    except (TypeError, ValueError):
        return False


def _require_post(db: Session, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise ParentPostNotFoundError("Post not found")
    return post


def get_comments(
    db: Session,
    post_id: int,
    *,
    page: int,
    size: int,
) -> tuple[list[Comment], int]:
    try:
        _require_post(db, post_id)
        total = db.scalar(
            select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
        ) or 0
        items = list(
            db.scalars(
                select(Comment)
                .where(Comment.post_id == post_id)
                .order_by(Comment.created_at.asc(), Comment.id.asc())
                .offset((page - 1) * size)
                .limit(size)
            ).all()
        )
        return items, total
    except ParentPostNotFoundError:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to read comments due to a database error")
        raise CommentServiceError("Comments could not be read") from exc


def create_comment(db: Session, post_id: int, data: CommentCreate) -> Comment:
    try:
        _require_post(db, post_id)
        comment = Comment(
            post_id=post_id,
            nickname=data.nickname,
            content=data.content,
            password_hash=_hash_password(data.password),
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
    except ParentPostNotFoundError:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to create a comment due to a database error")
        raise CommentServiceError("Comment could not be created") from exc


def delete_comment(db: Session, post_id: int, comment_id: int, password: str) -> None:
    try:
        _require_post(db, post_id)
        comment = db.scalar(
            select(Comment).where(Comment.id == comment_id, Comment.post_id == post_id)
        )
        if comment is None:
            raise CommentNotFoundError("Comment not found")
        if not _verify_password(password, comment.password_hash):
            raise IncorrectCommentPasswordError("Incorrect password")
        db.delete(comment)
        db.commit()
    except (ParentPostNotFoundError, CommentNotFoundError, IncorrectCommentPasswordError):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to delete a comment due to a database error")
        raise CommentServiceError("Comment could not be deleted") from exc


def add_like(db: Session, post_id: int) -> int:
    try:
        _require_post(db, post_id)
        db.add(PostLike(post_id=post_id))
        db.commit()
        return db.scalar(
            select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)
        ) or 0
    except ParentPostNotFoundError:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to add a like due to a database error")
        raise CommentServiceError("Like could not be added") from exc
