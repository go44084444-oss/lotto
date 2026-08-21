from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401 — Base.metadata에 모든 모델을 등록
from app.config import settings
from app.db.base import Base
from app.db.session import get_db


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    root, _, dbname = settings.database_url.rpartition("/")
    return f"{root}/{dbname}_test"


def _ensure_database_exists(test_url: str) -> None:
    root, _, dbname = test_url.rpartition("/")
    admin_engine = create_engine(f"{root}/postgres", isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": dbname}
        ).first()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{dbname}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    test_url = _test_database_url()
    _ensure_database_exists(test_url)
    engine = create_engine(test_url, future=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def _reset_db(test_engine: Engine) -> Iterator[None]:
    """매 테스트 전: 전체 테이블 비우기 + 운영 마이그레이션과 동일한 기본 'free' 티어 시드."""
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.execute(
            Base.metadata.tables["membership_tiers"].insert(),
            {"code": "free", "weekly_quota": 20, "display_name": "무료 회원"},
        )
    yield


@pytest.fixture()
def db_session(test_engine: Engine) -> Iterator[Session]:
    session_factory = sessionmaker(bind=test_engine, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(test_engine: Engine) -> Iterator[TestClient]:
    from app.main import app  # 지연 임포트 — app 임포트 시점에 라우터/스케줄러가 로드됨

    session_factory = sessionmaker(bind=test_engine, future=True)

    def _override_get_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
