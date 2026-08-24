from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.jobs import scheduler
from app.routers import admin, assignments, auth, draws, me, push


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="로또 조합 배분 API",
    description=(
        "45개 중 6개를 뽑는 조합 중 '패턴이 뚜렷한' 조합만 걸러 회원에게 주 단위로 "
        "중복 없이 배분한다. 이 필터링은 당첨 확률을 높이지 않으며, 확률과 무관한 "
        "필터임을 명시한다."
    ),
    lifespan=lifespan,
)

_origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(assignments.router)
app.include_router(draws.router)
app.include_router(admin.router)
app.include_router(push.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
