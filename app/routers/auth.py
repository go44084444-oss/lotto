from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.member import Member
from app.schemas.auth import LoginIn, RegisterIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    member = Member(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(member)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 이메일입니다."
        ) from exc
    db.refresh(member)
    return TokenOut(access_token=create_access_token(member.id))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다."
    )
    member = db.query(Member).filter(Member.email == payload.email).first()
    if member is None or not verify_password(payload.password, member.hashed_password):
        raise unauthorized
    return TokenOut(access_token=create_access_token(member.id))
