"""당첨 알림 발송 서비스. 지금은 웹 푸시(Web Push) 채널만 구현한다. 카카오톡 알림톡 등
다른 채널을 추가할 때는 NotificationChannel을 구현해 _channels에 더하면 된다."""

from __future__ import annotations

import json
import logging
from typing import Protocol

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.config import settings
from app.models.member import Member
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


class NotificationChannel(Protocol):
    def send(self, db: Session, member: Member, title: str, body: str) -> None: ...


class WebPushChannel:
    """VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY가 설정되어 있어야 동작한다. 설정 전에는
    조용히 건너뛴다(개발 중/키 미발급 상태에서도 나머지 기능이 죽지 않도록)."""

    def send(self, db: Session, member: Member, title: str, body: str) -> None:
        if not settings.vapid_private_key or not settings.vapid_public_key:
            logger.warning("VAPID 키가 설정되지 않아 웹 푸시를 건너뜀 (member_id=%s)", member.id)
            return

        subscriptions = (
            db.query(PushSubscription).filter(PushSubscription.member_id == member.id).all()
        )
        payload = json.dumps({"title": title, "body": body})

        for sub in subscriptions:
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            }
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=settings.vapid_private_key,
                    vapid_claims={"sub": settings.vapid_subject},
                )
            except WebPushException as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code in (404, 410):
                    db.delete(sub)
                    db.commit()
                else:
                    logger.warning("웹 푸시 발송 실패 (member_id=%s): %s", member.id, exc)


_channels: list[NotificationChannel] = [WebPushChannel()]


def notify_win(db: Session, member: Member, draw_no: int, best_rank: int, win_count: int) -> None:
    title = f"{draw_no}회차 당첨 알림"
    if win_count == 1:
        body = f"배정 조합 중 {best_rank}등 당첨이 있습니다. 앱에서 확인해보세요."
    else:
        body = f"배정 조합 중 {win_count}개가 당첨(최고 {best_rank}등)됐습니다. 앱에서 확인해보세요."
    for channel in _channels:
        channel.send(db, member, title, body)
