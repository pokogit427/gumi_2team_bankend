# 커밋 컨벤션 규칙

이 문서는 Git 커밋 메시지를 일관되게 작성하기 위한 일반적인 규칙을 정리합니다. 명확한 커밋 메시지는 코드 변경 이력을 이해하기 쉽게 하고 협업 생산성을 높입니다.

## 1. 커밋 메시지 구조

커밋 메시지는 다음 구조를 따릅니다.

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 1.1 type
커밋 유형을 명시합니다. 대표적인 유형은 다음과 같습니다.

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅, 세미콜론 누락, 코드 변경 없는 수정
- `refactor`: 리팩토링
- `perf`: 성능 개선
- `test`: 테스트 추가/수정
- `chore`: 빌드 업무 수정, 패키지 매니저 설정, 기타 잡무
- `ci`: CI 설정 및 배포 스크립트 변경
- `build`: 빌드 관련 변경
- `revert`: 이전 커밋 되돌리기

### 1.2 scope
변경 영역을 선택적으로 명시합니다.

예시:
- `api`
- `ui`
- `auth`
- `database`
- `docs`

scope는 선택 사항이며, 구체적인 모듈 또는 기능 이름을 사용할 수 있습니다.

### 1.3 subject
한 문장으로 변경 내용을 요약합니다.
- 소문자로 시작합니다.
- 마침표로 끝나지 않습니다.
- 명령형 문장 형태로 작성합니다.

예시:
- `fix(api): handle empty response payload`
- `feat(ui): add search filter buttons`

## 2. 본문(body)

본문은 선택 사항이지만 변경 내용이 복잡하거나 이유를 설명해야 할 때 작성합니다.

- 변경 이유와 배경
- 어떤 문제가 있었는지
- 어떻게 해결했는지
- 추가로 참고해야 할 사항

본문은 빈 줄로 구분된 문단 형태로 작성합니다.

## 3. 꼬리말(footer)

꼬리말은 다음과 같은 경우에 사용합니다.

- 이슈 번호 참조: `Closes #123`, `Fixes #45`
- 브레이킹 체인지: `BREAKING CHANGE: ...`
- 기타 메타 정보

## 4. 작성 예시

```
feat(search): add category chip filter

Use category chips to filter search results by tourism, restaurant,
festival, and community posts.

Closes #102
```

```
fix(board): validate password before delete request

Prevent deletion when the provided password is missing or incorrect.

BREAKING CHANGE: password validation now returns 400 instead of 200 on failure.
```

```
docs: update README with deployment instructions

Add Netlify and Render deployment steps and environment variable examples.
```

## 5. 추가 규칙

- 커밋 메시지는 영어로 작성하는 것이 좋습니다. 협업 시 일관성이 좋아집니다.
- 작은 단위로 자주 커밋합니다.
- 하나의 커밋에는 하나 가지 변경 목적을 담습니다.
- 코드 변경이 없는 문서/설정 수정도 커밋으로 남깁니다.
- 불필요하게 긴 subject는 피하고, 핵심 내용을 간결하게 전달합니다.

## 6. 금지 사항

- `WIP`, `temp`, `fix typo`처럼 의미가 불명확한 커밋 메시지
- 커밋 메시지에 상세 코드 내용을 그대로 복사
- 여러 가지 변경 내용을 한 커밋에 섞는 것
- 커밋 제목과 본문의 내용이 불일치하는 것
