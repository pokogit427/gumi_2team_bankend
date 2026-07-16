"""HTTP endpoints for community posts."""

from fastapi import APIRouter, Depends, Query, Path, status
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
    error = ErrorResponse(code="server_error", message="Internal server error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump(),
    )


@router.get(
    "",
    response_model=PostListResponse,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}},
    description=(
        "게시글 목록을 페이지 단위로 조회합니다."
        " `page`와 `size` 쿼리 파라미터로 페이징을 조절할 수 있으며,"
        " 각 항목은 `PostResponse` 스키마를 따릅니다."
    ),
)
def list_posts_endpoint(
    page: int = Query(default=1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수 (1-100)"),
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
    description=(
        "단일 게시글을 조회하고 조회수를 1 증가시킵니다."
        " 존재하지 않는 게시글 id로 요청하면 `not_found` 오류를 반환합니다."
    ),
)
def get_post_endpoint(post_id: int = Path(..., description="조회할 게시글의 ID"), db: Session = Depends(get_db)):
    try:
        return get_post_and_increment_view_count(db, post_id)
    except PostNotFoundError:
        error = ErrorResponse(code="not_found", message="Post not found")
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
    description=(
        "게시글을 수정합니다. 요청 바디의 `password`가 원래 게시글의 비밀번호와 일치해야 합니다."
        " 실패 시 적절한 에러 코드와 메시지를 반환합니다."
    ),
)
def update_post_endpoint(
    post_data: PostUpdate,
    post_id: int = Path(..., description="수정할 게시글의 ID"),
    db: Session = Depends(get_db),
):
    try:
        return update_post(db, post_id, post_data)
    except PostNotFoundError:
        error = ErrorResponse(code="not_found", message="Post not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )
    except IncorrectPostPasswordError:
        error = ErrorResponse(code="forbidden", message="Incorrect password")
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
    description=(
        "게시글을 삭제합니다. 요청 바디에 `password`를 포함해야 하며,"
        " 비밀번호 검증에 실패하면 `forbidden` 에러를 반환합니다."
    ),
)
def delete_post_endpoint(
    delete_data: PostDeleteRequest,
    post_id: int = Path(..., description="삭제할 게시글의 ID"),
    db: Session = Depends(get_db),
):
    try:
        delete_post(db, post_id, delete_data)
        return {"message": "Post deleted"}
    except PostNotFoundError:
        error = ErrorResponse(code="not_found", message="Post not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )
    except IncorrectPostPasswordError:
        error = ErrorResponse(code="forbidden", message="Incorrect password")
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
    description=(
        "새 게시글을 작성합니다. 응답으로 생성된 게시글의 전체 정보를 반환합니다."
        " 비밀번호는 향후 수정/삭제 확인용으로 평문으로 저장됩니다(프로덕션에서는 해시 권장)."
    ),
)
def create_post_endpoint(post_data: PostCreate, db: Session = Depends(get_db)):
    try:
        return create_post(db, post_data)
    except PostCreationError:
        return _server_error_response()
