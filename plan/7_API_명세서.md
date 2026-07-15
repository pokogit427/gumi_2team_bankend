# 7_API_명세서

이 문서는 LocalHub 백엔드의 API 명세를 정리한 문서다. 구현 전 기준으로 작성되었으며, 프론트엔드와 백엔드가 동일한 스펙을 사용하도록 한다.

---

## 공통 규칙

- 모든 API는 JSON으로 요청/응답한다.
- 게시글 작성 입력은 `title`, `content`, `password`를 사용한다.
- 게시글 수정 입력은 `title`, `content`, `password`를 사용한다.
- 게시글 삭제 입력은 `password`를 사용한다.
- 비밀번호는 응답에서 절대 노출하지 않는다.
- 목록 응답은 `items`, `total`, `page`, `size`를 포함한다.
- 지역정보 검색 파라미터는 `query`, `category`를 사용한다.
- 통합 검색 결과는 `result_type`으로 `location`과 `post`를 구분한다.
- 챗봇 요청은 `message` 필드를 사용한다.
- 챗봇 응답은 `answer`와 `references`를 포함한다.
- 잘못된 비밀번호는 `403`으로 응답한다.
- 없는 데이터는 `404`로 응답한다.
- 잘못된 요청은 `400` 또는 `422`로 응답한다.
- 서버 내부 오류는 상세 내용을 노출하지 않는다.
- 검색 결과가 없으면 `200`과 빈 `items` 배열을 반환한다.
- Query Parameter 이름은 코드와 문서에서 일관되게 사용한다.

---

## 1. GET /health

### 기능명
서버 상태 확인

### HTTP Method
GET

### URL
/health

### Path Parameter
없음

### Query Parameter
없음

### Request Body
없음

### 성공 Response
```json
{
  "status": "ok"
}
```

### 오류 Response
```json
{
  "error": "server_error",
  "message": "Internal server error"
}
```

### HTTP 상태 코드
- 200 OK
- 500 Internal Server Error

### 데이터 소스
없음

### 프론트엔드 사용 화면
- 앱 진입 시 서버 연결 상태 확인

### 예시 요청
```http
GET /health
```

### 예시 응답
```json
{
  "status": "ok"
}
```

---

## 2. GET /api/posts

### 기능명
게시글 목록 조회

### HTTP Method
GET

### URL
/api/posts

### Path Parameter
없음

### Query Parameter
- `page` (optional, integer): 페이지 번호
- `size` (optional, integer): 한 페이지당 항목 수

### Request Body
없음

### 성공 Response
```json
{
  "items": [
    {
      "id": 1,
      "title": "구미 여행 후기",
      "content": "좋았어요",
      "created_at": "2026-07-15T10:00:00",
      "updated_at": "2026-07-15T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

### 오류 Response
```json
{
  "error": "invalid_request",
  "message": "Invalid query parameters"
}
```

### HTTP 상태 코드
- 200 OK
- 400 Bad Request
- 422 Unprocessable Entity

### 데이터 소스
SQLite `posts` 테이블

### 프론트엔드 사용 화면
- 게시판 목록 화면

### 예시 요청
```http
GET /api/posts?page=1&size=10
```

### 예시 응답
```json
{
  "items": [
    {
      "id": 1,
      "title": "구미 여행 후기",
      "content": "좋았어요",
      "created_at": "2026-07-15T10:00:00",
      "updated_at": "2026-07-15T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

---

## 3. GET /api/posts/{post_id}

### 기능명
게시글 상세 조회

### HTTP Method
GET

### URL
/api/posts/{post_id}

### Path Parameter
- `post_id` (required, integer): 게시글 ID

### Query Parameter
없음

### Request Body
없음

### 성공 Response
```json
{
  "id": 1,
  "title": "구미 여행 후기",
  "content": "좋았어요",
  "created_at": "2026-07-15T10:00:00",
  "updated_at": "2026-07-15T10:00:00"
}
```

### 오류 Response
```json
{
  "error": "not_found",
  "message": "Post not found"
}
```

### HTTP 상태 코드
- 200 OK
- 404 Not Found

### 데이터 소스
SQLite `posts` 테이블

### 프론트엔드 사용 화면
- 게시글 상세 화면

### 예시 요청
```http
GET /api/posts/1
```

### 예시 응답
```json
{
  "id": 1,
  "title": "구미 여행 후기",
  "content": "좋았어요",
  "created_at": "2026-07-15T10:00:00",
  "updated_at": "2026-07-15T10:00:00"
}
```

---

## 4. POST /api/posts

### 기능명
게시글 생성

### HTTP Method
POST

### URL
/api/posts

### Path Parameter
없음

### Query Parameter
없음

### Request Body
```json
{
  "title": "구미 여행 후기",
  "content": "좋았어요",
  "password": "1234"
}
```

### 성공 Response
```json
{
  "id": 1,
  "title": "구미 여행 후기",
  "content": "좋았어요",
  "created_at": "2026-07-15T10:00:00",
  "updated_at": "2026-07-15T10:00:00"
}
```

### 오류 Response
```json
{
  "error": "invalid_request",
  "message": "title, content, and password are required"
}
```

### HTTP 상태 코드
- 201 Created
- 400 Bad Request
- 422 Unprocessable Entity

### 데이터 소스
SQLite `posts` 테이블

### 프론트엔드 사용 화면
- 게시글 작성 화면

### 예시 요청
```http
POST /api/posts
Content-Type: application/json

{
  "title": "구미 여행 후기",
  "content": "좋았어요",
  "password": "1234"
}
```

### 예시 응답
```json
{
  "id": 1,
  "title": "구미 여행 후기",
  "content": "좋았어요",
  "created_at": "2026-07-15T10:00:00",
  "updated_at": "2026-07-15T10:00:00"
}
```

---

## 5. PUT /api/posts/{post_id}

### 기능명
게시글 수정

### HTTP Method
PUT

### URL
/api/posts/{post_id}

### Path Parameter
- `post_id` (required, integer): 게시글 ID

### Query Parameter
없음

### Request Body
```json
{
  "title": "수정된 제목",
  "content": "수정된 내용",
  "password": "1234"
}
```

### 성공 Response
```json
{
  "id": 1,
  "title": "수정된 제목",
  "content": "수정된 내용",
  "created_at": "2026-07-15T10:00:00",
  "updated_at": "2026-07-15T10:00:01"
}
```

### 오류 Response
```json
{
  "error": "forbidden",
  "message": "Incorrect password"
}
```

### HTTP 상태 코드
- 200 OK
- 400 Bad Request
- 403 Forbidden
- 404 Not Found
- 422 Unprocessable Entity

### 데이터 소스
SQLite `posts` 테이블

### 프론트엔드 사용 화면
- 게시글 수정 화면

### 예시 요청
```http
PUT /api/posts/1
Content-Type: application/json

{
  "title": "수정된 제목",
  "content": "수정된 내용",
  "password": "1234"
}
```

### 예시 응답
```json
{
  "id": 1,
  "title": "수정된 제목",
  "content": "수정된 내용",
  "created_at": "2026-07-15T10:00:00",
  "updated_at": "2026-07-15T10:00:01"
}
```

---

## 6. DELETE /api/posts/{post_id}

### 기능명
게시글 삭제

### HTTP Method
DELETE

### URL
/api/posts/{post_id}

### Path Parameter
- `post_id` (required, integer): 게시글 ID

### Query Parameter
없음

### Request Body
```json
{
  "password": "1234"
}
```

### 성공 Response
```json
{
  "message": "Post deleted"
}
```

### 오류 Response
```json
{
  "error": "forbidden",
  "message": "Incorrect password"
}
```

### HTTP 상태 코드
- 200 OK
- 400 Bad Request
- 403 Forbidden
- 404 Not Found

### 데이터 소스
SQLite `posts` 테이블

### 프론트엔드 사용 화면
- 게시글 삭제 확인 모달

### 예시 요청
```http
DELETE /api/posts/1
Content-Type: application/json

{
  "password": "1234"
}
```

### 예시 응답
```json
{
  "message": "Post deleted"
}
```

---

## 7. GET /api/locations

### 기능명
지역정보 목록 조회

### HTTP Method
GET

### URL
/api/locations

### Path Parameter
없음

### Query Parameter
- `query` (optional, string): 제목/주소/설명 키워드 검색어
- `category` (optional, string): 카테고리 필터

### Request Body
없음

### 성공 Response
```json
{
  "items": [
    {
      "id": "3032819",
      "title": "검성지 생태공원",
      "category": "관광지",
      "address": "경상북도 구미시 황상동",
      "latitude": 36.114844,
      "longitude": 128.438086,
      "image_url": null,
      "content_type_id": 12,
      "result_type": "location"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

### 오류 Response
```json
{
  "error": "invalid_request",
  "message": "Invalid query parameters"
}
```

### HTTP 상태 코드
- 200 OK
- 400 Bad Request
- 422 Unprocessable Entity

### 데이터 소스
data 폴더 JSON 파일 (`items` 배열)

### 프론트엔드 사용 화면
- 지역정보 목록 화면
- 검색 결과 화면

### 예시 요청
```http
GET /api/locations?query=구미&category=관광지
```

### 예시 응답
```json
{
  "items": [
    {
      "id": "3032819",
      "title": "검성지 생태공원",
      "category": "관광지",
      "address": "경상북도 구미시 황상동",
      "latitude": 36.114844,
      "longitude": 128.438086,
      "image_url": null,
      "content_type_id": 12,
      "result_type": "location"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

---

## 8. GET /api/locations/{content_id}

### 기능명
지역정보 상세 조회

### HTTP Method
GET

### URL
/api/locations/{content_id}

### Path Parameter
- `content_id` (required, string): 지역정보 고유 ID

### Query Parameter
없음

### Request Body
없음

### 성공 Response
```json
{
  "id": "3032819",
  "title": "검성지 생태공원",
  "category": "관광지",
  "address": "경상북도 구미시 황상동",
  "latitude": 36.114844,
  "longitude": 128.438086,
  "image_url": null,
  "content_type_id": 12,
  "result_type": "location"
}
```

### 오류 Response
```json
{
  "error": "not_found",
  "message": "Location not found"
}
```

### HTTP 상태 코드
- 200 OK
- 404 Not Found

### 데이터 소스
data 폴더 JSON 파일 (`items` 배열)

### 프론트엔드 사용 화면
- 지역정보 상세 화면

### 예시 요청
```http
GET /api/locations/3032819
```

### 예시 응답
```json
{
  "id": "3032819",
  "title": "검성지 생태공원",
  "category": "관광지",
  "address": "경상북도 구미시 황상동",
  "latitude": 36.114844,
  "longitude": 128.438086,
  "image_url": null,
  "content_type_id": 12,
  "result_type": "location"
}
```

---

## 9. GET /api/search

### 기능명
통합 검색

### HTTP Method
GET

### URL
/api/search

### Path Parameter
없음

### Query Parameter
- `query` (required, string): 검색어
- `category` (optional, string): 카테고리 필터

### Request Body
없음

### 성공 Response
```json
{
  "items": [
    {
      "id": "3032819",
      "title": "검성지 생태공원",
      "result_type": "location",
      "category": "관광지"
    },
    {
      "id": 1,
      "title": "구미 여행 후기",
      "result_type": "post",
      "category": "community"
    }
  ],
  "total": 2,
  "page": 1,
  "size": 10
}
```

### 오류 Response
```json
{
  "error": "invalid_request",
  "message": "query is required"
}
```

### HTTP 상태 코드
- 200 OK
- 400 Bad Request
- 422 Unprocessable Entity

### 데이터 소스
- data 폴더 JSON 파일 (`items` 배열)
- SQLite `posts` 테이블

### 프론트엔드 사용 화면
- 홈/검색 결과 화면
- 통합 검색 화면

### 예시 요청
```http
GET /api/search?query=구미&category=all
```

### 예시 응답
```json
{
  "items": [
    {
      "id": "3032819",
      "title": "검성지 생태공원",
      "result_type": "location",
      "category": "관광지"
    },
    {
      "id": 1,
      "title": "구미 여행 후기",
      "result_type": "post",
      "category": "community"
    }
  ],
  "total": 2,
  "page": 1,
  "size": 10
}
```

---

## 10. POST /api/chat

### 기능명
챗봇 질의 응답

### HTTP Method
POST

### URL
/api/chat

### Path Parameter
없음

### Query Parameter
없음

### Request Body
```json
{
  "message": "구미에서 가볼 만한 관광지 추천해줘"
}
```

### 성공 Response
```json
{
  "answer": "구미 지역에서 검성지 생태공원 같은 관광지를 추천해 드릴게요.",
  "references": [
    {
      "id": "3032819",
      "title": "검성지 생태공원",
      "result_type": "location"
    }
  ]
}
```

### 오류 Response
```json
{
  "error": "invalid_request",
  "message": "message is required"
}
```

### HTTP 상태 코드
- 200 OK
- 400 Bad Request
- 422 Unprocessable Entity
- 500 Internal Server Error

### 데이터 소스
- data 폴더 JSON 파일 (`items` 배열)
- SQLite `posts` 테이블

### 프론트엔드 사용 화면
- 챗봇 플로팅 위젯
- 챗봇 대화 화면

### 예시 요청
```http
POST /api/chat
Content-Type: application/json

{
  "message": "구미에서 가볼 만한 관광지 추천해줘"
}
```

### 예시 응답
```json
{
  "answer": "구미 지역에서 검성지 생태공원 같은 관광지를 추천해 드릴게요.",
  "references": [
    {
      "id": "3032819",
      "title": "검성지 생태공원",
      "result_type": "location"
    }
  ]
}
```

---

## 프론트엔드와 합의가 필요한 부분

다음 항목은 프론트엔드와 사전에 합의가 필요하다.

1. 목록 응답의 `page`, `size` 기본값
2. `id` 값의 타입을 문자열로 유지할지, 숫자로 통일할지
3. 지역정보 응답의 필드명(`image_url` vs `imageUrl`)
4. 게시글 응답의 날짜 필드명(`created_at` vs `createdAt`)
5. 검색 API의 `category` 기본값(`all` 또는 `null`)
6. 챗봇 응답의 `references` 구성 방식
7. 에러 응답 포맷의 일관성

---

## 확정한 API 목록

1. GET /health
2. GET /api/posts
3. GET /api/posts/{post_id}
4. POST /api/posts
5. PUT /api/posts/{post_id}
6. DELETE /api/posts/{post_id}
7. GET /api/locations
8. GET /api/locations/{content_id}
9. GET /api/search
10. POST /api/chat
