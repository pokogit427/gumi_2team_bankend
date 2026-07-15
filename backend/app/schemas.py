from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseTextModel(BaseModel):
    @field_validator("title", "content", "password", "message", mode="before", check_fields=False)
    @classmethod
    def strip_and_validate(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class PostCreate(BaseTextModel):
    """새 게시글 작성 시 사용되는 요청 바디 스키마.

    - `title`: 게시글 제목
    - `content`: 게시글 본문
    - `password`: 게시글 수정/삭제를 위한 비밀번호(평문)
    """
    title: str = Field(..., min_length=1, max_length=200, description="게시글 제목 (1-200자)")
    content: str = Field(..., min_length=1, max_length=5000, description="게시글 본문 (1-5000자)")
    password: str = Field(..., min_length=1, max_length=100, description="수정/삭제용 비밀번호 (평문)")


class PostUpdate(BaseTextModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    password: str = Field(..., min_length=1, max_length=100)


class PostDeleteRequest(BaseTextModel):
    password: str = Field(..., min_length=1, max_length=100)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """게시글 응답 모델: DB에서 반환되는 게시글 정보를 포함합니다."""

    id: int = Field(..., description="게시글 고유 ID")
    title: str = Field(..., description="게시글 제목")
    content: str = Field(..., description="게시글 본문")
    created_at: datetime = Field(..., description="생성일시 (UTC)")
    updated_at: datetime = Field(..., description="수정일시 (UTC)")


class PostListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[PostResponse]
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """지역정보 응답 모델: JSON 데이터셋에서 정규화한 지역(관광지/음식점/축제) 정보."""

    id: int | str = Field(..., description="데이터셋 내 콘텐츠 고유 ID")
    title: str = Field(..., description="장소명")
    category: str = Field(..., description="카테고리 (예: 관광지, 음식점, 축제공연행사)")
    address: str | None = Field(default=None, description="주소")
    overview: str | None = Field(default=None, description="간단 소개/요약")
    latitude: float | None = Field(default=None, description="위도")
    longitude: float | None = Field(default=None, description="경도")
    image_url: str | None = Field(default=None, description="이미지 URL")
    thumbnail_url: str | None = Field(default=None, description="썸네일 URL")
    telephone: str | None = Field(default=None, description="전화번호")
    content_type_id: int | None = Field(default=None, description="콘텐츠 유형 ID")
    source: str | None = Field(default=None, description="출처 파일명 또는 데이터셋")
    license: str | None = Field(default=None, description="저작권/라이선스 정보")
    collected_at: str | None = Field(default=None, description="수집 일시")
    result_type: Literal["location"] = Field(default="location", description="항목 유형: location")


class LocationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[LocationResponse]
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """통합 검색 결과 항목.

    `result_type`으로 `location` 또는 `post`를 구분합니다.
    """

    id: int | str = Field(..., description="검색 결과의 고유 ID")
    title: str = Field(..., description="결과 제목")
    summary: str = Field(..., description="간단 요약")
    result_type: Literal["location", "post"] = Field(..., description="결과 유형")
    category: str | None = Field(default=None, description="카테고리(지역 항목의 경우)")
    source: str | None = Field(default=None, description="출처 정보")
    license: str | None = Field(default=None, description="라이선스 정보")
    collected_at: str | None = Field(default=None, description="수집 일시")


class SearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[SearchResult]
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class ChatRequest(BaseTextModel):
    message: str = Field(..., min_length=1, max_length=500, description="챗봇에게 묻고 싶은 질문 또는 요청 텍스트")


class ChatReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | str = Field(..., description="참조 항목의 ID")
    title: str = Field(..., description="참조 항목 제목")
    result_type: Literal["location", "post"] = Field(..., description="참조 항목 유형")


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    answer: str = Field(..., description="챗봇이 생성한 자연어 응답")
    references: list[ChatReference] = Field(default_factory=list, description="챗봇이 참조한 항목 목록")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """표준 에러 응답 형식.

    - `error`: 간단한 에러 코드
    - `message`: 사람에게 읽기 쉬운 설명
    """

    error: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
