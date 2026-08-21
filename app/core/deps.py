from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.member import Member

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_member(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Member:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증이 필요합니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    member_id = decode_access_token(credentials.credentials)
    if member_id is None:
        raise unauthorized

    member = db.get(Member, member_id)
    if member is None:
        raise unauthorized

    return member
