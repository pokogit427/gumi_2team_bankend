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
    # 관광 관련 키워드: 포함되는 다양한 표현을 포괄하도록 확장
    if any(k in text for k in ("관광", "추천", "여행", "볼 만", "가볼", "가볼만", "명소", "추천해줘", "추천해주세요")):
        return "tourist"
    if any(k in text for k in ("축제", "행사", "일정")):
        return "festival"
    if any(k in text for k in ("맛집", "음식", "식당", "경치", "뷰", "카페", "한식", "양식", "분위기")):
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
        line = f"{index}. [{ref['result_type']}] {ref.get('title', '')}"
        if ref.get("snippet"):
            line += f" - {ref['snippet']}"
        if ref.get("file"):
            line += f" (file: {ref['file']})"
        lines.append(line)
    return "\n".join(lines)


def _build_reference_from_local_data(item: dict) -> dict:
    """로컬 JSON 데이터 항목을 ChatReference 형태로 변환합니다."""
    return {
        "id": item.get("id"),
        "title": item.get("title", item.get("file", "local_data")),
        "snippet": item.get("snippet"),
        "file": item.get("file"),
        "result_type": "local_data",
    }


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
            "당신은 구미 지역 관광 및 맛집 정보를 잘 아는 한국어 안내자입니다."
            "\n사용자의 질문에 대해 자연스럽고 친절하게 답변하세요."
            "\n가능한 경우, 아래 참조 항목을 반영하되 과도하게 길지 않게 요약해 주세요."
            "\n\n"
            f"질문: {message}\n\n"
            f"{_format_references_for_prompt(references)}\n\n"
            "답변:"
        )

        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            max_output_tokens=2048,
            text={"format": {"type": "text"}},
        )
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text

        def extract_text(item):
            if item is None:
                return []
            if isinstance(item, str):
                return [item]
            if isinstance(item, (list, tuple)):
                results = []
                for sub in item:
                    results.extend(extract_text(sub))
                return results
            if hasattr(item, "to_dict") and not isinstance(item, dict):
                try:
                    return extract_text(item.to_dict())
                except Exception:
                    pass
            if isinstance(item, dict):
                results = []
                if isinstance(item.get("text"), str):
                    results.append(item["text"])
                content = item.get("content")
                if content is not None:
                    results.extend(extract_text(content))
                message = item.get("message")
                if message is not None:
                    results.extend(extract_text(message))
                return results
            results = []
            text_value = getattr(item, "text", None)
            if isinstance(text_value, str):
                results.append(text_value)
            content_value = getattr(item, "content", None)
            if content_value is not None:
                results.extend(extract_text(content_value))
            message_value = getattr(item, "message", None)
            if message_value is not None:
                results.extend(extract_text(message_value))
            return results

        output = getattr(response, "output", None)
        texts = extract_text(output)
        if texts:
            return "\n".join(texts).strip()

        if hasattr(response, "text") and isinstance(response.text, str) and response.text:
            return response.text

        # `response.text` may be a ResponseTextConfig object in some SDK versions,
        # so we fallback to a dictionary-based extraction if needed.
        response_dict = response.to_dict()
        output_items = response_dict.get("output")
        texts = extract_text(output_items)
        if texts:
            return "\n".join(texts).strip()

        return "죄송합니다. 응답을 생성하는 동안 오류를 발생했습니다. 다시 시도해 주세요."
    except Exception:
        # 재시도나 세부 에러 처리를 호출자에게 맡깁니다.
        raise


def _search_local_json_files(query: str, max_hits: int = 5) -> list[dict]:
    """`backend/data/*.json` 파일을 검색해 쿼리와 매칭되는 항목을 최대 `max_hits`개 반환합니다.

    반환되는 항목 형태: {"id": <str>, "title": <str>, "snippet": <str>, "file": <str>, "result_type": "local_data"}
    이 함수는 안전성 때문에 파일 전체를 프롬프트로 보내지 않고, 매칭된 필드의 간단한 스니펫만 제공합니다.
    """
    try:
        from pathlib import Path
        import json
    except Exception:
        return []

    data_dir = Path(__file__).resolve().parents[2] / "data"
    if not data_dir.exists():
        return []

    matches = []
    q = query.casefold()
    for p in data_dir.glob("*.json"):
        if len(matches) >= max_hits:
            break
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        items = raw if isinstance(raw, list) else [raw]
        for idx, item in enumerate(items):
            if len(matches) >= max_hits:
                break
            # find candidate string fields
            candidate = None
            for key in ("title", "name", "description", "addr", "category"): 
                val = item.get(key) if isinstance(item, dict) else None
                if isinstance(val, str) and q in val.casefold():
                    candidate = (key, val)
                    break
            if not candidate:
                # fallback: search any string fields (cheap scan)
                if isinstance(item, dict):
                    for k, v in item.items():
                        if isinstance(v, str) and q in v.casefold():
                            candidate = (k, v)
                            break
            if candidate:
                key, val = candidate
                title = item.get("title") or item.get("name") or p.stem
                snippet = val if len(val) <= 200 else val[:197] + "..."
                matches.append({
                    "id": f"{p.name}:{idx}",
                    "title": title,
                    "snippet": snippet,
                    "file": p.name,
                    "result_type": "local_data",
                })

    return matches


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
            # 전체 문장으로 매칭이 없으면 메시지에서 핵심 토큰을 추출해 부분 검색합니다.
            if not refs:
                import re

                tokens = [t for t in re.findall(r"[\w가-힣]+", message) if len(t) >= 2]
                seen_ids = set()
                refs = []
                for tok in tokens:
                    locs = filter_locations(query=tok, category="관광지")
                    for loc in locs:
                        if loc.get("id") in seen_ids:
                            continue
                        refs.append(_build_reference_from_location(loc))
                        seen_ids.add(loc.get("id"))
                        if len(refs) >= max_refs:
                            break
                    if len(refs) >= max_refs:
                        break

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
