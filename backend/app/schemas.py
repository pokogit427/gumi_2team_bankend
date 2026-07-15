from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseTextModel(BaseModel):
    @field_validator("title", "content", "password", mode="before", check_fields=False)
    @classmethod
    def strip_and_validate(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class PostCreate(BaseTextModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    password: str = Field(..., min_length=1, max_length=100)


class PostUpdate(BaseTextModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    password: str = Field(..., min_length=1, max_length=100)


class PostDeleteRequest(BaseTextModel):
    password: str = Field(..., min_length=1, max_length=100)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[PostResponse]
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | str
    title: str
    category: str
    address: str | None = None
    overview: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    telephone: str | None = None
    content_type_id: int | None = None
    source: str | None = None
    license: str | None = None
    collected_at: str | None = None
    result_type: Literal["location"] = "location"


class LocationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[LocationResponse]
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | str
    title: str
    summary: str
    result_type: Literal["location", "post"]
    category: str | None = None
    source: str | None = None
    license: str | None = None
    collected_at: str | None = None


class SearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[SearchResult]
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class ChatRequest(BaseTextModel):
    message: str = Field(..., min_length=1, max_length=500)


class ChatReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | str
    title: str
    result_type: Literal["location", "post"]


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    references: list[ChatReference] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    error: str
    message: str
