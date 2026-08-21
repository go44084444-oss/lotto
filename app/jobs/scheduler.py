"""주간 리셋 잡. 정확한 컷오버 시각은 미확정이므로 config.py의 WEEK_RESET_* 값을
그대로 쓴다(TODO(product)). 스케줄러가 죽어도 week_service.get_or_create_current_cycle이
요청 시점에 복구하므로, 이 잡은 정확한 시각에 리셋이 '보통' 일어나게 하는 역할이다."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.db.session import SessionLocal
from app.services import week_service

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_rollover() -> None:
    with SessionLocal() as db:
        cycle = week_service.rollover(db)
        logger.info("주간 롤오버 완료: 새 cycle_key=%s", cycle.cycle_key)


def start() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    hour, minute = (int(x) for x in settings.week_reset_time.split(":"))
    trigger = CronTrigger(
        day_of_week=settings.week_reset_day_of_week,
        hour=hour,
        minute=minute,
        timezone=settings.week_reset_timezone,
    )
    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_rollover, trigger, id="weekly_rollover", replace_existing=True)
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
