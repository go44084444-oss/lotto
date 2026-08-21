# 로또 조합 배분 API

로또 6/45 조합을 8개 규칙으로 필터링해 회원에게 주 단위로 중복 없이 배분하는 API 서버.
스펙 원문은 `CLAUDE_1.md`, 구현 계획은 `C:\Users\go550\.claude\plans\reflective-painting-kahan.md` 참고.

## 준비

```powershell
docker compose up -d
uv run alembic upgrade head
```

## 데이터 수집 및 조합 풀 생성 (최초 1회)

```powershell
uv run python -m scripts.ingest_superkts      # 1~1234회 (superkts.com 엑셀)
uv run python -m scripts.ingest_dhlottery     # 1235회~ (동행복권 API)
uv run python -m scripts.generate_pool        # 8개 필터 적용, ~3,645,902개 적재
```

`ingest_dhlottery.py`는 동행복권 사이트가 자동화된 요청에 대기실/차단 페이지를 반환하는
경우 우회하지 않고 즉시 실패로 보고한다. 실패하면 사이트 접근 가능 여부를 직접 확인할 것.

## 서버 실행

```powershell
uv run uvicorn app.main:app --reload
```

`http://127.0.0.1:8000/docs`에서 API 문서 확인 가능.

## 테스트

```powershell
uv run pytest
```

- `test_filters.py` — 8개 필터 규칙 단위 테스트 + 1237회 실제 당첨번호(10,20,23,34,37,40)가
  필터를 통과하는지 확인
- `test_pool_generation.py` — 전체 814만 5,060개 조합 중 필터 생존 조합이 정확히
  3,645,902개인지 확인 (DB 불필요, 수십 초 소요)
- `test_assignment_concurrency.py` — 동시 요청 시 같은 주 내 조합 중복 배정이 없는지 확인
- `test_api_*.py` — API 엔드포인트 계약 테스트

테스트는 `DATABASE_URL`과 같은 서버의 `_test` 접미사 DB(예: `lotto_test`)를 자동 생성해 사용한다.

## 하드 제약

- 이 필터링은 당첨 확률을 높이지 않는다. 어떤 문서/주석/API 응답에도 "확률 향상"으로
  표현하지 않는다.
- 과거 당첨 조합을 판매 풀에서 제외하는 로직을 추가하지 않는다(이미 검토 후 기각됨).

## 미확정 사항 (TODO)

- 주간 리셋 정확한 컷오버 시각 — `app/config.py`의 `WEEK_RESET_*` 참고.
- 탈퇴 회원의 배정 조합 반납 여부 — `app/routers/members.py`의 `withdraw_member` 참고.
