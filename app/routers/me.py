from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_member
from app.db.session import get_db
from app.models.member import Member
from app.schemas.member import MemberOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MemberOut)
def get_me(member: Member = Depends(get_current_member)) -> Member:
    return member


@router.post("/withdraw", response_model=MemberOut)
def withdraw_me(
    member: Member = Depends(get_current_member), db: Session = Depends(get_db)
) -> Member:
    if member.status == "active":
        # TODO(product): 탈퇴 회원의 이번 주 배정 조합을 반납할지 여부 미정.
        # 현재는 assignments를 건드리지 않고 회원 상태만 변경한다.
        member.status = "withdrawn"
        member.withdrawn_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(member)
    return member
