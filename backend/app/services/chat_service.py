"""Rule-based chat service for generating simple answers.

이 서비스는 OpenAI 등의 외부 AI를 호출하지 않고 로컬 데이터만으로
규칙 기반 응답을 생성합니다. 주요 흐름:
1. 메시지를 간단히 분류(키워드 기반)
2. 분류 유형에 따라 지역정보 또는 게시글을 검색
3. 요약형 답변과 최대 N개의 참조 항목을 반환

클래스/함수는 초보자가 이해하기 쉬운 수준으로 자세한 docstring을 포함합니다.
"""

from typing import List

from app.config import settings
import app.services.location_service as location_service
import app.services.post_service as post_service

# 테스트 편의성: 외부에서 `app.services.chat_service.filter_locations`처럼
# 직접 패치할 수 있도록 모듈 수준 alias를 제공합니다.
filter_locations = location_service.filter_locations
search_posts = post_service.search_posts


class ChatServiceError(RuntimeError):
    """챗봇 서비스 내부 오류를 나타내는 예외입니다.

    라우터에서 이 예외를 잡아 500 응답을 반환하도록 설계되어 있습니다.
    """


def _classify_message(message: str) -> str:
    """간단한 키워드 기반 분류기.

    반환값은 다음 중 하나입니다: 'tourist', 'festival', 'restaurant', 'post', 'unknown'

    로직은 아주 단순하며 메시지에 특정 키워드가 포함되어 있으면 그 카테고리를 반환합니다.
    이 방식은 규칙 기반으로 챗봇 동작을 빠르게 구현/테스트하기 위함입니다.
    """
    text = message.casefold()
    if any(k in text for k in ("관광", "추천", "여행", "볼 만")):
        return "tourist"
    if any(k in text for k in ("축제", "행사", "일정")):
        return "festival"
    if any(k in text for k in ("맛집", "음식", "식당")):
        return "restaurant"
    if any(k in text for k in ("글", "게시글", "후기", "포스트")):
        return "post"
    return "unknown"


def _build_reference_from_location(loc: dict) -> dict:
    """지역정보 항목을 ChatReference 형태(사전)로 변환합니다.

    ChatReference는 `id`, `title`, `result_type`을 포함합니다.
    """
    return {"id": loc.get("id"), "title": loc.get("title"), "result_type": "location"}


def _build_reference_from_post(post) -> dict:
    """게시글 ORM 객체를 ChatReference 형태(사전)로 변환합니다."""
    return {"id": post.id, "title": post.title, "result_type": "post"}


def _format_references_for_prompt(references: list[dict]) -> str:
    """프롬프트에 넣을 참조 목록 텍스트로 변환합니다."""
    if not references:
        return ""
    lines = ["참조 항목:"]
    for index, ref in enumerate(references, start=1):
        lines.append(f"{index}. [{ref['result_type']}] {ref['title']}")
    return "\n".join(lines)


def _generate_openai_answer(message: str, references: list[dict]) -> str:
    """OpenAI 응답을 생성합니다. 설정에 `openai_api_key`가 있어야 합니다.

    실패하면 예외를 던집니다 — 호출부에서 안전하게 처리하세요.
    """
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key is not configured")

    try:
        # import locally to avoid import error when dependency missing
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = (
            "아래 질문에 답해주세요. 가능한 경우 참조 항목을 반영하여 한국어로 간결하게 설명하고, "
            "질문에 직접 관련된 정보를 중심으로 답변하세요.\n\n"
            f"질문: {message}\n\n"
            f"{_format_references_for_prompt(references)}\n\n"
            "답변:"
        )

        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            max_output_tokens=512,
        )
        return getattr(response, "output_text", str(response))
    except Exception:
        # 재시도나 세부 에러 처리를 호출자에게 맡깁니다.
        raise


def generate_chat_response(message: str, db=None, max_refs: int = 5) -> dict:
    """주어진 메시지에 대해 규칙 기반 응답을 생성합니다.

    반환값은 Pydantic `ChatResponse`로 파싱 가능한 dict 형태입니다:
    { "answer": str, "references": [ {id, title, result_type}, ... ] }

    동작 과정:
    1. 메시지 분류
    2. 분류에 맞는 검색 수행
    3. 간단한 요약 텍스트(answer) 생성 및 참조 목록 구성

    예외 발생 시 `ChatServiceError`를 발생시켜 라우터가 500을 반환하게 합니다.
    """
    category = _classify_message(message)
    try:
        if category == "tourist":
            locations = filter_locations(query=message, category="관광지")
            refs = [_build_reference_from_location(loc) for loc in locations[:max_refs]]
            answer = f"추천 관광지를 찾았습니다: {', '.join([r['title'] for r in refs])}" if refs else "추천할 관광지를 찾지 못했습니다."
        elif category == "festival":
            locations = filter_locations(query=message, category="축제공연행사")
            refs = [_build_reference_from_location(loc) for loc in locations[:max_refs]]
            answer = f"관련 축제 정보를 찾았습니다: {', '.join([r['title'] for r in refs])}" if refs else "관련 축제 정보를 찾지 못했습니다."
        elif category == "restaurant":
            locations = filter_locations(query=message, category="음식점")
            refs = [_build_reference_from_location(loc) for loc in locations[:max_refs]]
            answer = f"추천 음식점: {', '.join([r['title'] for r in refs])}" if refs else "추천 음식점을 찾지 못했습니다."
        elif category == "post":
            # 게시글은 DB 검색(ORM 객체 리스트)을 반환. 이 경우 DB 세션이 필요합니다.
            if db is None:
                raise ChatServiceError("DB session required for post searches")
            posts = search_posts(db, message)
            refs = [_build_reference_from_post(p) for p in posts[:max_refs]]
            answer = f"관련 게시글을 찾았습니다: {', '.join([r['title'] for r in refs])}" if refs else "관련 게시글을 찾지 못했습니다."
        else:
            refs = []
            answer = "질문을 이해하지 못했습니다. 관광지, 축제, 음식점, 게시글 관련 질문을 해보세요."

        # OpenAI 키가 설정되어 있으면 AI에게 더 자연스러운 응답을 요청합니다.
        if settings.openai_api_key:
            try:
                ai_answer = _generate_openai_answer(message, refs)
                # OpenAI 응답이 비어있으면 규칙 기반 답변 유지
                if ai_answer:
                    answer = ai_answer
            except Exception:
                # 외부 호출 실패 시 규칙 기반 답변을 사용합니다.
                pass

        return {"answer": answer, "references": refs}
    except Exception as exc:
        # 내부 예외는 외부로 감추고 일관된 오류로 처리
        raise ChatServiceError("Chat service failed") from exc
