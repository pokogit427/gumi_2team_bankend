"""Router for chatbot endpoint.

이 모듈은 `POST /api/chat` 엔드포인트를 제공하며, 요청을 받아 규칙 기반의
응답을 생성하는 `chat_service`를 호출합니다. 실제 외부 AI 호출은 하지 않고
로컬 데이터(지역정보 및 게시글)를 기반으로 간단한 답변을 만듭니다.
"""

from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.chat_service import (
    ChatServiceError,
    generate_chat_response,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """POST /api/chat

    사용자가 입력한 `message`를 간단한 키워드 규칙으로 분류하여 관련 지역정보
    또는 게시글을 찾아 요약적 답변(`answer`)과 최대 N개의 참조(`references`)를 반환합니다.

    이 엔드포인트는 외부 AI 호출을 하지 않는 규칙 기반 구현입니다. 실제 AI 연동은
    별도의 플래그 및 보안 검토 후 추가하세요.
    """
    try:
        response = generate_chat_response(request.message, db=db)
        return response
    except ChatServiceError:
        error = ErrorResponse(code="server_error", message="Internal server error")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error.model_dump())
