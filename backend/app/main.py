import logging
import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.models import Post  # noqa: F401
from app.routers.locations import router as locations_router
from app.routers.posts import router as posts_router
from app.routers.search import router as search_router
from app.routers.chat import router as chat_router
from app.schemas import ErrorResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("localhub")


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(title="LocalHub API")


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


@app.on_event("startup")
def create_tables() -> None:
    """애플리케이션 시작 시 데이터베이스 테이블을 생성합니다.

    SQLAlchemy의 `Base.metadata.create_all`을 호출하여 필요한 테이블을 생성합니다.
    이 작업은 idempotent 하며 이미 테이블이 존재하면 아무 동작도 수행하지 않습니다.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization completed")


@app.get("/health")
def health_check() -> dict[str, str]:
    """헬스체크 엔드포인트.

    클라이언트가 서버 상태를 확인할 때 사용합니다. 단순히 상태 문자열을 반환합니다.
    """
    return {"status": "ok"}
