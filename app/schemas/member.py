from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    status: str
    tier: str
    created_at: datetime
