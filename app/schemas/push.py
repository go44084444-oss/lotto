from pydantic import BaseModel


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    """브라우저 PushManager.subscribe() 결과(PushSubscriptionJSON)를 그대로 받는다."""

    endpoint: str
    keys: PushSubscriptionKeys


class VapidPublicKeyOut(BaseModel):
    vapid_public_key: str
