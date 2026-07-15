# Deployment Guide (Render)

## 목적
Render에 `LocalHub` FastAPI 백엔드를 배포하기 위한 최소 설정과 주의사항을 정리합니다.

## 기본 설정
- Repository: GitHub (연동)
- Branch: `dev2` (또는 배포용 브랜치)
- Root Directory: `backend`

## Build Command
```bash
pip install -r requirements.txt
```

## Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 환경변수
- `DATABASE_URL`: 예: `sqlite:///./localhub.db` (Render에서는 컨테이너 파일시스템 특성상 영속성에 주의)
- `ALLOWED_ORIGINS`: Netlify와 로컬을 쉼표로 구분해 지정 (예: `http://localhost:5173,https://your-app.netlify.app`)
- `ENV`, `DEBUG` 등

## SQLite 영속성 주의사항
- Render의 Web Service는 재배포/재시작 시 파일시스템이 변경될 수 있어 SQLite 파일이 유실될 가능성이 있습니다.
- 데모·MVP 용도로는 허용하되 운영 데이터는 외부 DB(Postgres)로 이전 권장.
- 제출용 `.db` 파일은 로컬에서 별도 생성·보관하여 제출하세요.

## Health & Docs
- `/health` 엔드포인트로 서비스 상태 확인
- `/docs`에서 Swagger UI 확인

## CORS
- `ALLOWED_ORIGINS`에 Netlify Origin을 추가하세요.

## 배포 순서 요약
1. 코드를 push
2. Render에서 서비스 생성 및 GitHub repo 연결
3. Root directory를 `backend`로 설정
4. Build & Start Command 입력
5. 환경변수 등록
6. Deploy 실행 및 `/health`, `/docs` 확인
