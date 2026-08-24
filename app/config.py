from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://lotto:lotto@localhost:5432/lotto"

    @field_validator("database_url")
    @classmethod
    def _ensure_psycopg_driver(cls, v: str) -> str:
        """Railway 등 managed Postgres가 주는 DATABASE_URL은 드라이버 접미사가 없는
        `postgres://`/`postgresql://` 형태다. SQLAlchemy가 psycopg3를 쓰도록 보정한다."""
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://") :]
        return v

    # 주간 리셋 컷오버 — 잠정값. TODO(product): 토요일 추첨 결과 확정 시각 기준으로 재확인 필요.
    week_reset_day_of_week: str = "sat"
    week_reset_time: str = "21:00"
    week_reset_timezone: str = "Asia/Seoul"

    default_weekly_quota: int = 20

    superkts_download_url: str = "https://superkts.com/lotto/download"
    dhlottery_api_url: str = (
        "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
    )

    admin_api_key: str = "change-me-in-production"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 14  # 14일 — 리프레시 토큰 없음(v1)

    cors_allowed_origins: str = "http://localhost:5173"

    # 웹 푸시(VAPID) — 비어 있으면 발송 시도 시 명확한 에러로 실패한다.
    # 생성: uv run vapid --gen (py-vapid 패키지, pywebpush 의존성으로 함께 설치됨)
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@example.com"


settings = Settings()
