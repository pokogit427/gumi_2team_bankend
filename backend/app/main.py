import logging

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.models import Post  # noqa: F401
from app.routers.locations import router as locations_router
from app.routers.posts import router as posts_router
from app.routers.search import router as search_router
from app.schemas import ErrorResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("localhub")

app = FastAPI(title="LocalHub API")
app.include_router(locations_router)
app.include_router(posts_router)
app.include_router(search_router)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization completed")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
