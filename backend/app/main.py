import logging
import os
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import Base, engine, ensure_schema_compatibility
from app.models import Post  # noqa: F401
from app.routers.locations import router as locations_router
from app.routers.posts import router as posts_router
from app.routers.search import router as search_router
from app.routers.chat import router as chat_router
from app.routers.comments import router as comments_router
from app.schemas import ErrorResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("localhub")


# OpenAPI 태그 메타데이터: 각 태그별 설명을 추가하면 Swagger UI의 사이드바에 노출됩니다.
tags_metadata = [
    {
        "name": "posts",
        "description": "게시글 CRUD API: 작성, 조회, 수정, 삭제 기능을 제공합니다. 비밀번호로 수정/삭제 권한을 검증합니다.",
    },
    {
        "name": "locations",
        "description": "지역정보 API: 데이터셋으로부터 정규화된 관광지/음식점/축제 정보를 조회합니다. 카테고리·검색·페이징을 지원합니다.",
    },
    {
        "name": "search",
        "description": "통합 검색 API: 게시글과 지역정보를 통합하여 키워드 기반 검색 결과를 제공합니다. 카테고리 필터와 페이징을 지원합니다.",
    },
    {
        "name": "chat",
        "description": "규칙 기반 챗봇 API: 간단한 질문을 분류해 지역정보 또는 게시글을 참조해 응답을 생성합니다. 외부 AI 호출은 하지 않습니다.",
    },
    {
        "name": "health",
        "description": "서비스 헬스체크 엔드포인트입니다.",
    },
]


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="LocalHub API",
    description=(
        "LocalHub는 지역 관광지, 음식점, 축제 정보와 커뮤니티 게시판을 제공하는 백엔드 API입니다."
        " 이 문서에는 각 엔드포인트의 사용법, 요청/응답 스키마, 에러 포맷이 포함되어 있습니다."
    ),
    version="0.1.0",
    openapi_tags=tags_metadata,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"code": "validation_error", "message": "Invalid request"},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == status.HTTP_404_NOT_FOUND else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": str(exc.detail)},
    )


# CORS 설정
# 우선순위: 환경변수 ALLOWED_ORIGINS > 기존 settings.cors_origins
# 여러 origin은 쉼표(,)로 구분하여 전달할 수 있다.
# 보안: 전체 허용("*")은 사용하지 않도록 강제한다.
def _get_allowed_origins() -> List[str]:
    """환경변수 `ALLOWED_ORIGINS` 또는 설정의 `cors_origins` 값을 파싱해
    CORS 허용 origin 리스트를 반환합니다.

    반환값은 각 origin의 앞뒤 공백을 제거한 문자열 리스트입니다.
    만약 값에 '*'가 포함되어 있으면 빈 리스트를 반환하여 전체 허용을 방지합니다.
    이 함수는 환경변수 값을 로그에 출력하지 않도록 주의합니다.
    """
    origins_raw = os.environ.get("ALLOWED_ORIGINS") or getattr(settings, "cors_origins", "")
    if not origins_raw:
        return []

    # 쉼표로 분리하고 각 항목을 정리
    origins = [o.strip() for o in origins_raw.split(",") if o.strip()]

    # 보안 규칙: 전체 허용('*')은 허용하지 않음
    if any(o == "*" for o in origins):
        logger.warning("Wildcard '*' found in ALLOWED_ORIGINS; treating as empty list for security")
        return []

    return origins


# CORS 미들웨어 등록 — 필요한 HTTP 메서드 및 헤더만 허용
allowed_origins = _get_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    allow_credentials=False,  # 쿠키/자격증명 미사용(설명: 이 프로젝트는 로그인 쿠키를 사용하지 않음)
)


# 라우터 등록
app.include_router(locations_router)
app.include_router(posts_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(comments_router)


@app.on_event("startup")
def create_tables() -> None:
    """애플리케이션 시작 시 데이터베이스 테이블을 생성합니다.

    SQLAlchemy의 `Base.metadata.create_all`을 호출하여 필요한 테이블을 생성합니다.
    이 작업은 idempotent 하며 이미 테이블이 존재하면 아무 동작도 수행하지 않습니다.
    """
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()
    logger.info("Database initialization completed")


@app.get("/health")
def health_check() -> dict[str, str]:
    """헬스체크 엔드포인트.

    서비스의 기본 동작 여부를 확인하기 위한 간단한 엔드포인트입니다. 모니터링 툴이나
    로드밸런서가 주기적으로 호출하여 서비스 상태를 확인할 수 있습니다. HTTP 200과
    JSON `{ "status": "ok" }`을 반환하면 정상 상태로 간주합니다.
    """
    return {"status": "ok"}
