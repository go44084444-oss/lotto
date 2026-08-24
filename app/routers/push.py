from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_member
from app.db.session import get_db
from app.models.member import Member
from app.models.push_subscription import PushSubscription
from app.schemas.push import PushSubscriptionIn, VapidPublicKeyOut

router = APIRouter(tags=["push"])


@router.get("/push/vapid-public-key", response_model=VapidPublicKeyOut)
def get_vapid_public_key() -> VapidPublicKeyOut:
    return VapidPublicKeyOut(vapid_public_key=settings.vapid_public_key)


@router.post(
    "/me/push-subscriptions",
    status_code=status.HTTP_204_NO_CONTENT,
    description="브라우저 PushManager.subscribe() 결과를 등록/갱신한다(endpoint 기준 upsert).",
)
def create_push_subscription(
    payload: PushSubscriptionIn,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> Response:
    existing = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == payload.endpoint)
        .first()
    )
    if existing is not None:
        existing.member_id = member.id
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
    else:
        db.add(
            PushSubscription(
                member_id=member.id,
                endpoint=payload.endpoint,
                p256dh=payload.keys.p256dh,
                auth=payload.keys.auth,
            )
        )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/me/push-subscriptions",
    status_code=status.HTTP_204_NO_CONTENT,
    description="이 브라우저의 구독을 해제한다.",
)
def delete_push_subscription(
    endpoint: str,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> Response:
    db.query(PushSubscription).filter(
        PushSubscription.endpoint == endpoint, PushSubscription.member_id == member.id
    ).delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
