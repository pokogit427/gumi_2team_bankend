 # 개발 계획서 (Development Plan)

 ## 한줄 개요
 LocalHub 백엔드의 남은 작업(18단계~26단계)을 우선순위 기반 스프린트로 정리한 실행 계획서입니다.

 ## 목표
- 납기 기준의 핵심 기능(게시판 CRUD, 지역정보 API, 통합 검색, 챗봇, CORS, 테스트, 배포) 완료
- 자동화된 pytest 통과 및 배포 준비 문서화

## 주요 산출물
- 완성된 API 구현(backend/app/*)
- 자동화 테스트(`tests/`)
- 배포 문서(`backend/DEPLOYMENT.md`)
- 프론트 연동 가이드(`plan/12_프론트엔드_연동가이드.md`)

## 스프린트 계획 (우선순위 기반)

- Sprint 0 — 준비 (완료)
  - 작업: 가상환경 생성, requirements 설치, plan/* 검토
  - 산출물: `backend/.venv` 설치, 의존성 설치

- Sprint 1 — 설정·DB (0.5일)
  - 작업: `app/config.py` (.env.example 업데이트 포함), `app/database.py`, DB URL 분리
  - 검증: `/health` 정상, DB 접속 성공

- Sprint 2 — 게시판 CRUD (1일)
  - 작업: `models.Post`, `schemas`, `services/post_service.py`, `routers/posts.py`
  - 검증: CRUD API, 비밀번호 미노출, 조회수 증가, 관련 pytest 통과

- Sprint 3 — 지역정보 로더·API (0.5일)
  - 작업: `services/location_service.py`, `routers/locations.py`, JSON 캐시·좌표 변환
  - 검증: 목록/상세/카테고리/결측값 케이스 통과

- Sprint 4 — 통합 검색·챗봇 (0.5~1일)
  - 작업: `services/search_service.py`, `routers/search.py`, `services/chat_service.py`, `POST /api/chat`(규칙 기반)
  - 검증: 검색 결과 `result_type` 분리, 챗봇 주요 질의 응답, OpenAI 호출 없음(모킹)

- Sprint 5 — CORS·배포 준비·문서화 (0.5일)
  - 작업: `app/main.py` CORS 설정(`ALLOWED_ORIGINS` 환경변수 파싱), `backend/DEPLOYMENT.md`, `plan/12_프론트엔드_연동가이드.md` 작성
  - 검증: `http://localhost:5173`에서 호출 가능, 허용하지 않은 Origin 차단 문서화

- Sprint 6 — 테스트·회귀·최종 점검 (0.5일)
  - 작업: 전체 `pytest -v` 실행, 실패 항목 수정, 테스트 리포트 작성
  - 검증: 주요 테스트 통과 또는 상세 이슈 목록화

## 우선순위 요약
- 최우선: 게시판 CRUD, 지역정보 로더, 통합 검색
- 중간: 챗봇(규칙 기반), pytest 자동화
- 후순위: 배포 튜닝, 문서 보강

## 리스크 및 대응
- SQLite 영속성(재시작 시 유실): `backend/DEPLOYMENT.md`에 Render 주의사항 명시 및 제출용 `.db` 별도 보관 권장
- 민감정보 유출: `.env`는 Git에 포함 금지, 로그에 값 출력 금지
- OpenAI 호출 비용/한도: 실제 호출 대신 모킹 권장

## 빠른 실행 명령 (로컬)
```bash
cd backend
# PowerShell
.venv\Scripts\Activate.ps1
# cmd
backend\.venv\Scripts\activate
# Git Bash
source backend/.venv/Scripts/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 테스트 실행
```bash
cd backend
source backend/.venv\Scripts\activate  # 또는 각 환경에 맞게
pytest -v
```

## 다음 권장 작업 (제가 도와드릴 수 있음)
1. Sprint 1 코드화 (`app/config.py`, `.env.example` 업데이트)
2. Sprint 2 게시판 CRUD 구현 및 pytest 작성
3. `plan/12_프론트엔드_연동가이드.md` 생성

## 커밋 분할 기준 (간단)
- 설정/인프라: `app/config.py`, `.env.example` 변경 — `feat(config): ...`
- 데이터 모델/DB: `app/models.py`, `app/database.py` — `feat(database): ...`
- 게시판(Posts): 라우터, 서비스, 스키마, 테스트 포함 — `feat(posts): ...`
- 지역정보(Locations): 로더, 라우터, 스키마, 테스트 포함 — `feat(locations): ...`
- 통합검색(Search): 라우터·서비스·테스트 포함 — `feat(search): ...`
- 챗봇(Chat): 별도 브랜치에서 구현 및 테스트 — `feat(chat): ...`
- CORS/배포/문서: `app/main.py`, `backend/DEPLOYMENT.md`, `plan/*` — `chore(deploy): ...` 또는 `docs: ...`

## 현재 구현 상태 (요약)
- 구현 완료: `GET /health`, 게시판 CRUD, 지역정보 목록/상세, 통합 검색
- 테스트: 게시판·지역정보·검색 관련 pytest 존재
- 미구현 / 보강 필요: `POST /api/chat`(챗봇), CORS 미적용(코드 추가 필요), `.env` 변수명 통일(`ALLOWED_ORIGINS` vs `cors_origins`), 배포 문서 보강

## 권장 즉시 작업
1. CORS 미들웨어 추가 및 `.env.example`에 `ALLOWED_ORIGINS` 예시 추가
2. 챗봇 엔드포인트 골격 추가(규칙 기반) 및 기본 테스트 작성
3. 배포 문서(`backend/DEPLOYMENT.md`)와 프론트 연동 가이드 초안 작성

---
작성자: 팀 개발 계획 자동 생성기
변경일: 2026-07-15
