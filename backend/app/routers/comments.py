"""HTTP endpoints for anonymous comments and post likes."""

from fastapi import APIRouter, Depends, Path, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CommentCreate,
    CommentDeleteRequest,
    CommentListResponse,
    CommentResponse,
    ErrorResponse,
    LikeResponse,
)
from app.services.comment_service import (
    CommentNotFoundError,
    CommentServiceError,
    IncorrectCommentPasswordError,
    ParentPostNotFoundError,
    add_like,
    create_comment,
    delete_comment,
    get_comments,
)

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(code=code, message=message).model_dump(),
    )


@router.get("/{post_id}/comments", response_model=CommentListResponse)
def list_comments_endpoint(
    post_id: int = Path(..., ge=1),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        items, total = get_comments(db, post_id, page=page, size=size)
        return CommentListResponse(items=items, total=total, page=page, size=size)
    except ParentPostNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, "not_found", "Post not found")
    except CommentServiceError:
        return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "server_error", "Internal server error")


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment_endpoint(
    data: CommentCreate,
    post_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    try:
        return create_comment(db, post_id, data)
    except ParentPostNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, "not_found", "Post not found")
    except CommentServiceError:
        return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "server_error", "Internal server error")


@router.delete("/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment_endpoint(
    data: CommentDeleteRequest,
    post_id: int = Path(..., ge=1),
    comment_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    try:
        delete_comment(db, post_id, comment_id, data.password)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ParentPostNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, "not_found", "Post not found")
    except CommentNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, "not_found", "Comment not found")
    except IncorrectCommentPasswordError:
        return _error(status.HTTP_403_FORBIDDEN, "invalid_password", "Incorrect password")
    except CommentServiceError:
        return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "server_error", "Internal server error")


@router.post("/{post_id}/likes", response_model=LikeResponse, include_in_schema=False)
@router.post("/{post_id}/like", response_model=LikeResponse)
def add_like_endpoint(
    post_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    try:
        count = add_like(db, post_id)
        return LikeResponse(post_id=post_id, likes=count, like_count=count)
    except ParentPostNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, "not_found", "Post not found")
    except CommentServiceError:
        return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "server_error", "Internal server error")
