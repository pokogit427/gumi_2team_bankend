"""HTTP endpoints for normalized location data."""

from fastapi import APIRouter, Query, Path, status
from fastapi.responses import JSONResponse

from app.schemas import ErrorResponse, LocationListResponse, LocationResponse
from app.services.location_service import (
    LocationDataError,
    get_location_by_content_id,
    get_location_page,
)

router = APIRouter(prefix="/api/locations", tags=["locations"])


def _data_error_response() -> JSONResponse:
    error = ErrorResponse(code="server_error", message="Internal server error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump(),
    )


@router.get(
    "",
    response_model=LocationListResponse,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}},
    description=(
        "지역정보 목록을 조회합니다. `query`로 텍스트 검색을 수행하고 `category`로 필터링할 수 있습니다."
        " 결과는 페이지네이션되어 반환됩니다."
    ),
)
def list_locations_endpoint(
    query: str | None = Query(default=None, max_length=200, description="검색어(이름/설명 등)"),
    category: str | None = Query(default=None, max_length=50, description="카테고리 필터(예: 관광지, 음식점, 축제공연행사)"),
    page: int = Query(default=1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수 (1-100)"),
):
    try:
        items, total = get_location_page(
            query=query,
            category=category,
            page=page,
            size=size,
        )
        return LocationListResponse(items=items, total=total, page=page, size=size)
    except LocationDataError:
        return _data_error_response()


@router.get(
    "/{content_id}",
    response_model=LocationResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
    description=(
        "단일 지역정보 항목을 `content_id`로 조회합니다."
        " 항목이 존재하지 않으면 `not_found` 오류를 반환합니다."
    ),
)
def get_location_endpoint(content_id: str = Path(..., description="조회할 콘텐츠의 content_id")):
    try:
        location = get_location_by_content_id(content_id)
    except LocationDataError:
        return _data_error_response()

    if location is None:
        error = ErrorResponse(code="not_found", message="Location not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )
    return location
