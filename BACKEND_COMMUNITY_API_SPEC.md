# LocalHub 게시판 상호작용 API 요청 명세

## 1. 목적

현재 프론트엔드에서 좋아요와 댓글은 브라우저 `localStorage`에만 저장되고, 조회수는 백엔드 응답에 포함되지 않아 항상 `0`으로 표시됩니다.

여러 사용자가 같은 좋아요·댓글·조회수를 공유할 수 있도록 아래 API와 DB 필드를 추가해 주세요.

기본 API 주소:

```text
https://gumi-2team-bankend-2.onrender.com/api
```

## 2. 공통 응답 규칙

- 모든 날짜는 ISO 8601 UTC 문자열로 반환합니다.
- 댓글 비밀번호와 비밀번호 해시는 어떤 응답에도 포함하지 않습니다.
- 좋아요 및 조회수 증가는 DB에서 원자적으로 처리합니다.
- 존재하지 않는 게시글과 댓글은 `404`를 반환합니다.
- 요청 검증 오류는 기존 FastAPI 규칙에 맞춰 `422`를 사용할 수 있습니다.

공통 오류 응답 예시:

```json
{
  "code": "not_found",
  "message": "게시글을 찾을 수 없습니다."
}
```

## 3. 게시글 응답 모델 확장

기존 `PostResponse`와 게시글 목록의 각 항목에 아래 필드를 추가해 주세요.

```json
{
  "id": 1,
  "title": "금오산 산책 코스 추천",
  "content": "대혜폭포까지 걷기 좋습니다.",
  "views": 12,
  "likes": 5,
  "comment_count": 2,
  "created_at": "2026-07-16T01:30:00Z",
  "updated_at": "2026-07-16T01:30:00Z"
}
```

권장 DB 필드:

| 필드 | 타입 | 기본값 | 설명 |
|---|---:|---:|---|
| `views` | integer | `0` | 상세 조회 횟수 |
| `likes` | integer | `0` | 좋아요 횟수 |

`comment_count`는 댓글 테이블을 집계하거나 별도 카운터 필드로 관리할 수 있습니다.

## 4. 조회수 API

별도 조회수 API보다 기존 상세 조회 API에서 조회수를 증가시키는 방식을 권장합니다.

### 게시글 상세 조회 및 조회수 증가

```http
GET /api/posts/{post_id}
```

동작:

1. 게시글의 `views`를 원자적으로 1 증가시킵니다.
2. 증가된 조회수를 포함한 게시글을 반환합니다.

성공 응답: `200 OK`

```json
{
  "id": 1,
  "title": "금오산 산책 코스 추천",
  "content": "대혜폭포까지 걷기 좋습니다.",
  "views": 13,
  "likes": 5,
  "comment_count": 2,
  "created_at": "2026-07-16T01:30:00Z",
  "updated_at": "2026-07-16T01:30:00Z"
}
```

존재하지 않는 게시글: `404 Not Found`

```json
{
  "code": "not_found",
  "message": "게시글을 찾을 수 없습니다."
}
```

참고:

- 목록 조회 `GET /api/posts`에서는 조회수를 증가시키지 않습니다.
- 목록 응답에는 현재 `views`, `likes`, `comment_count`를 포함합니다.
- 중복 조회 방지는 필수 요구사항이 아닙니다. 필요하면 IP/세션/쿠키 기준 정책을 별도로 정할 수 있습니다.

## 5. 좋아요 API

### 게시글 좋아요 증가

```http
POST /api/posts/{post_id}/like
```

요청 본문은 없습니다.

성공 응답: `200 OK`

```json
{
  "post_id": 1,
  "likes": 6
}
```

존재하지 않는 게시글: `404 Not Found`

```json
{
  "code": "not_found",
  "message": "게시글을 찾을 수 없습니다."
}
```

구현 주의사항:

- `likes = likes + 1`은 원자적 UPDATE로 처리해 동시 요청 시 값이 유실되지 않게 합니다.
- 현재 프론트 요구사항은 로그인 없는 단순 누적 방식입니다.
- 사용자별 1회 제한이 필요하면 로그인, 익명 토큰 또는 별도의 좋아요 기록 테이블이 추가로 필요합니다.

## 6. 댓글 데이터 모델

권장 댓글 테이블:

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | integer | 댓글 고유 ID |
| `post_id` | integer | 게시글 외래 키 |
| `nickname` | varchar | 익명 닉네임 |
| `content` | text | 댓글 내용 |
| `password_hash` | varchar | 삭제 검증용 비밀번호 해시 |
| `created_at` | datetime | 작성 일시 |
| `updated_at` | datetime | 수정 일시 |

게시글이 삭제될 때 소속 댓글도 함께 삭제되도록 외래 키 `ON DELETE CASCADE` 사용을 권장합니다.

댓글 응답 모델:

```json
{
  "id": 101,
  "post_id": 1,
  "nickname": "금오산다람쥐",
  "content": "좋은 정보 감사합니다.",
  "created_at": "2026-07-16T02:00:00Z",
  "updated_at": "2026-07-16T02:00:00Z"
}
```

`password`와 `password_hash`는 응답에서 제외합니다.

## 7. 댓글 목록 API

```http
GET /api/posts/{post_id}/comments?page=1&size=50
```

성공 응답: `200 OK`

```json
{
  "items": [
    {
      "id": 101,
      "post_id": 1,
      "nickname": "금오산다람쥐",
      "content": "좋은 정보 감사합니다.",
      "created_at": "2026-07-16T02:00:00Z",
      "updated_at": "2026-07-16T02:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50
}
```

정렬은 오래된 댓글부터 표시하는 `created_at ASC`를 권장합니다.

## 8. 댓글 작성 API

```http
POST /api/posts/{post_id}/comments
Content-Type: application/json
```

요청 예시:

```json
{
  "nickname": "금오산다람쥐",
  "password": "1234",
  "content": "좋은 정보 감사합니다."
}
```

권장 검증 조건:

- `nickname`: 1~30자
- `password`: 4~100자
- `content`: 1~1000자
- 모든 문자열은 앞뒤 공백 제거 후 검증

성공 응답: `201 Created`

```json
{
  "id": 101,
  "post_id": 1,
  "nickname": "금오산다람쥐",
  "content": "좋은 정보 감사합니다.",
  "created_at": "2026-07-16T02:00:00Z",
  "updated_at": "2026-07-16T02:00:00Z"
}
```

댓글 비밀번호는 bcrypt 또는 Argon2 등으로 해시하여 저장합니다. 평문 비밀번호는 저장하지 않습니다.

## 9. 댓글 삭제 API

```http
DELETE /api/posts/{post_id}/comments/{comment_id}
Content-Type: application/json
```

요청 예시:

```json
{
  "password": "1234"
}
```

성공 응답 권장안: `204 No Content`

응답 본문은 없습니다.

비밀번호 불일치: `403 Forbidden`

```json
{
  "code": "invalid_password",
  "message": "댓글 비밀번호가 올바르지 않습니다."
}
```

댓글 또는 게시글 없음: `404 Not Found`

```json
{
  "code": "not_found",
  "message": "댓글을 찾을 수 없습니다."
}
```

삭제 시 `post_id`와 `comment_id`가 모두 일치하는 댓글만 대상으로 검증합니다.

## 10. 전체 엔드포인트 요약

| 기능 | Method | Endpoint | 성공 코드 |
|---|---|---|---:|
| 게시글 상세 + 조회수 증가 | GET | `/api/posts/{post_id}` | 200 |
| 좋아요 증가 | POST | `/api/posts/{post_id}/like` | 200 |
| 댓글 목록 | GET | `/api/posts/{post_id}/comments` | 200 |
| 댓글 작성 | POST | `/api/posts/{post_id}/comments` | 201 |
| 댓글 삭제 | DELETE | `/api/posts/{post_id}/comments/{comment_id}` | 204 |

## 11. 프론트엔드 연동 시 기대 필드

백엔드 구현 후 프론트에서는 다음 필드명을 그대로 사용할 예정입니다.

```text
post.id
post.views
post.likes
post.comment_count
comment.id
comment.post_id
comment.nickname
comment.content
comment.created_at
```

필드명이나 엔드포인트가 달라지는 경우 최종 OpenAPI 명세(`/openapi.json`)를 공유해 주세요. 해당 명세에 맞춰 프론트 API 계층을 수정할 수 있습니다.

## 12. 완료 확인용 테스트 시나리오

1. 게시글 상세를 두 번 조회했을 때 `views`가 각각 1씩 증가하는지 확인합니다.
2. 좋아요 API를 두 번 호출했을 때 `likes`가 각각 1씩 증가하는지 확인합니다.
3. 댓글 작성 후 댓글 목록과 `comment_count`에 반영되는지 확인합니다.
4. 잘못된 댓글 비밀번호로 삭제 시 `403`이 반환되는지 확인합니다.
5. 올바른 비밀번호로 삭제 시 `204`가 반환되고 목록에서 제거되는지 확인합니다.
6. 게시글 삭제 시 연결된 댓글도 함께 삭제되는지 확인합니다.
7. 동시 좋아요 요청에서도 증가 값이 유실되지 않는지 확인합니다.
