# 로또 조합 배분 API

로또 6/45 조합을 8개 규칙으로 필터링해 회원에게 주 단위로 중복 없이 배분하는 API 서버 + React 웹앱.
스펙 원문은 `CLAUDE_1.md`, 구현 계획은 `C:\Users\go550\.claude\plans\reflective-painting-kahan.md`,
인증/웹앱/배포 계획은 `C:\Users\go550\.claude\plans\quirky-sauteeing-engelbart.md` 참고.

## 준비

```powershell
copy .env.example .env
docker compose -p lotto-api up -d   # 폴더명에 한글/공백이 있어 -p로 프로젝트명을 명시해야 함
uv run alembic upgrade head
```

`.env`의 `JWT_SECRET_KEY`/`ADMIN_API_KEY`는 배포 시 반드시 실제 랜덤값으로 바꿀 것 — 기본값
(`change-me-in-production`)을 그대로 쓰지 않는다.

## 데이터 수집 및 조합 풀 생성 (최초 1회)

```powershell
uv run python -m scripts.ingest_superkts      # 1~1234회 (superkts.com 엑셀)
uv run python -m scripts.ingest_dhlottery     # 1235회~ (동행복권 API)
uv run python -m scripts.generate_pool        # 9개 필터 적용, ~3,570,443개 적재
```

`ingest_dhlottery.py`는 동행복권 사이트가 자동화된 요청에 대기실/차단 페이지를 반환하는
경우 우회하지 않고 즉시 실패로 보고한다. 실패하면 `POST /admin/draws`(관리자 API 키 필요)로
당첨번호를 수동 입력한다.

## 서버 실행

```powershell
uv run uvicorn app.main:app --reload
```

`http://127.0.0.1:8000/docs`에서 API 문서 확인 가능.

## 인증

이메일+비밀번호 기반 JWT 인증. 회원가입/로그인 시 발급된 토큰을 `Authorization: Bearer <token>`
헤더로 실어 `/me`, `/me/assignments/...` 등 회원 전용 엔드포인트를 호출한다.

- `POST /auth/register` — 회원가입, 가입과 동시에 토큰 발급
- `POST /auth/login` — 로그인, 토큰 발급
- `GET /me` / `POST /me/withdraw` — 내 정보 조회/탈퇴
- `POST /me/assignments`, `GET /me/assignments/current`, `GET /me/assignments/win-check` — 배정/당첨확인

`POST /admin/draws`, `POST /admin/weekly-cycles/rollover`는 회원 인증과 별개로
`X-Admin-Api-Key` 헤더(관리자 전용) 인증을 쓴다.

## 프론트엔드 (React)

```powershell
cd frontend
copy .env.example .env.local   # VITE_API_BASE_URL 확인
npm install
npm run dev
```

`http://localhost:5173`. 로컬 백엔드(`http://127.0.0.1:8000`)를 대상으로 동작하며,
`app/main.py`의 CORS 설정(`CORS_ALLOWED_ORIGINS`)에 이 주소가 포함되어 있어야 한다.

## Docker

```powershell
docker build -t lotto-api:local .
docker run -d --rm --network lotto-api_default -p 8000:8000 `
  -e DATABASE_URL="postgresql+psycopg://lotto:lotto@lotto-api-db-1:5432/lotto" `
  -e JWT_SECRET_KEY="..." -e ADMIN_API_KEY="..." -e CORS_ALLOWED_ORIGINS="..." `
  lotto-api:local
```

컨테이너 시작 시 `entrypoint.sh`가 `alembic upgrade head`를 먼저 실행한 뒤 서버를 띄운다.

## 배포 (Railway + Vercel)

백엔드+DB는 Railway(`railway.json`, `Dockerfile` 사용), 프론트는 Vercel(`frontend/vercel.json`)에
배포한다. Railway의 관리형 Postgres가 주는 `DATABASE_URL`은 드라이버 접미사가 없는 형태인데,
`app/config.py`의 `field_validator`가 `postgresql+psycopg://`로 자동 보정한다. 계정 생성·환경변수
설정·도메인 연결 등 대시보드 조작은 수동으로 진행해야 한다(자세한 절차는 위 구현 계획 문서 참고).

## 테스트

```powershell
uv run pytest
```

- `test_filters.py` — 8개 필터 규칙 단위 테스트 + 1237회 실제 당첨번호(10,20,23,34,37,40)가
  필터를 통과하는지 확인
- `test_pool_generation.py` — 전체 814만 5,060개 조합 중 필터 생존 조합이 정확히
  3,570,443개인지 확인 (DB 불필요, 수십 초 소요)
- `test_assignment_concurrency.py` — 동시 요청 시 같은 주 내 조합 중복 배정이 없는지 확인
- `test_api_*.py` — API 엔드포인트 계약 테스트 (인증/소유권 검증 포함)

테스트는 `DATABASE_URL`과 같은 서버의 `_test` 접미사 DB(예: `lotto_test`)를 자동 생성해 사용한다.
스키마를 바꾸는 마이그레이션을 추가했다면 기존 `_test` DB를 지워야 새 스키마로 재생성된다
(`create_all`은 기존 테이블을 변경하지 않음).

## 하드 제약

- 이 필터링은 당첨 확률을 높이지 않는다. 어떤 문서/주석/API 응답에도 "확률 향상"으로
  표현하지 않는다.
- 과거 당첨 조합을 판매 풀에서 제외하는 로직을 추가하지 않는다(이미 검토 후 기각됨).
- `.env`, `.env.local`, DB 접속정보, JWT/관리자 시크릿 절대 커밋 금지.

## 미확정 사항 (TODO)

- 주간 리셋 정확한 컷오버 시각 — `app/config.py`의 `WEEK_RESET_*` 참고.
- 탈퇴 회원의 배정 조합 반납 여부 — `app/routers/me.py`의 `withdraw_me` 참고.
- 이메일 인증/비밀번호 재설정 플로우 없음(v1 범위 밖, 친구들 대상 소규모 배포 전제).
