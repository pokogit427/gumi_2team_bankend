"""HTTP endpoints for community posts."""

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ErrorResponse,
    PostCreate,
    PostDeleteRequest,
    PostListResponse,
    PostResponse,
    PostUpdate,
)
from app.services.post_service import (
    IncorrectPostPasswordError,
    PostCreationError,
    PostNotFoundError,
    PostReadError,
    create_post,
    delete_post,
    get_post_and_increment_view_count,
    get_posts,
    update_post,
)

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _server_error_response() -> JSONResponse:
    error = ErrorResponse(error="server_error", message="Internal server error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump(),
    )


@router.get(
    "",
    response_model=PostListResponse,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}},
)
def list_posts_endpoint(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        items, total = get_posts(db, page=page, size=size)
        return PostListResponse(items=items, total=total, page=page, size=size)
    except PostReadError:
        return _server_error_response()


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
def get_post_endpoint(post_id: int, db: Session = Depends(get_db)):
    try:
        return get_post_and_increment_view_count(db, post_id)
    except PostNotFoundError:
        error = ErrorResponse(error="not_found", message="Post not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )
    except PostReadError:
        return _server_error_response()


@router.put(
    "/{post_id}",
    response_model=PostResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
def update_post_endpoint(
    post_id: int,
    post_data: PostUpdate,
    db: Session = Depends(get_db),
):
    try:
        return update_post(db, post_id, post_data)
    except PostNotFoundError:
        error = ErrorResponse(error="not_found", message="Post not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )
    except IncorrectPostPasswordError:
        error = ErrorResponse(error="forbidden", message="Incorrect password")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error.model_dump(),
        )
    except PostReadError:
        return _server_error_response()


@router.delete(
    "/{post_id}",
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
def delete_post_endpoint(
    post_id: int,
    delete_data: PostDeleteRequest,
    db: Session = Depends(get_db),
):
    try:
        delete_post(db, post_id, delete_data)
        return {"message": "Post deleted"}
    except PostNotFoundError:
        error = ErrorResponse(error="not_found", message="Post not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )
    except IncorrectPostPasswordError:
        error = ErrorResponse(error="forbidden", message="Incorrect password")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error.model_dump(),
        )
    except PostReadError:
        return _server_error_response()


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}},
)
def create_post_endpoint(post_data: PostCreate, db: Session = Depends(get_db)):
    try:
        return create_post(db, post_data)
    except PostCreationError:
        return _server_error_response()
