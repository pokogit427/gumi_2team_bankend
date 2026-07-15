"""HTTP endpoint for unified location and post search."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ErrorResponse, SearchResponse
from app.services.location_service import LocationDataError
from app.services.post_service import PostReadError
from app.services.search_service import search_all

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get(
    "",
    response_model=SearchResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
    description=(
        "키워드 기반 통합 검색을 수행합니다. `category`로 검색 대상을 제한할 수 있으며,"
        " 게시글과 지역정보가 함께 반환됩니다. `page`/`size`로 페이징을 조절하세요."
    ),
)
def search_endpoint(
    query: str = Query(min_length=1, max_length=200, description="검색어 (최소 1자)"),
    category: Literal["all", "tourist", "restaurant", "festival", "community"] = Query(
        "all",
        description="검색 대상: all(전체)/tourist/restaurant/festival/community",
    ),
    page: int = Query(default=1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수 (1-100)"),
    db: Session = Depends(get_db),
):
    query_text = query.strip()
    if not query_text:
        error = ErrorResponse(error="invalid_request", message="query is required")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error.model_dump(),
        )

    try:
        items, total = search_all(
            db,
            query=query_text,
            category=category,
            page=page,
            size=size,
        )
        return SearchResponse(items=items, total=total, page=page, size=size)
    except (LocationDataError, PostReadError):
        error = ErrorResponse(error="server_error", message="Internal server error")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error.model_dump(),
        )
