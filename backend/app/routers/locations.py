"""HTTP endpoints for normalized location data."""

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from app.schemas import ErrorResponse, LocationListResponse, LocationResponse
from app.services.location_service import (
    LocationDataError,
    get_location_by_content_id,
    get_location_page,
)

router = APIRouter(prefix="/api/locations", tags=["locations"])


def _data_error_response() -> JSONResponse:
    error = ErrorResponse(error="server_error", message="Internal server error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump(),
    )


@router.get(
    "",
    response_model=LocationListResponse,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}},
)
def list_locations_endpoint(
    query: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=50),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
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
)
def get_location_endpoint(content_id: str):
    try:
        location = get_location_by_content_id(content_id)
    except LocationDataError:
        return _data_error_response()

    if location is None:
        error = ErrorResponse(error="not_found", message="Location not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )
    return location
