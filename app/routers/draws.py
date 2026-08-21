from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.draw import Draw
from app.schemas.draw import DrawOut

router = APIRouter(prefix="/draws", tags=["draws"])


@router.get(
    "",
    response_model=list[DrawOut],
    description="과거 당첨번호 참고용 조회. 이 데이터는 조합 배분/필터링과 무관하다.",
)
def list_draws(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[Draw]:
    return db.query(Draw).order_by(desc(Draw.draw_no)).offset(offset).limit(limit).all()


@router.get("/latest", response_model=DrawOut)
def get_latest_draw(db: Session = Depends(get_db)) -> Draw:
    draw = db.query(Draw).order_by(desc(Draw.draw_no)).first()
    if draw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="당첨번호 데이터가 없습니다."
        )
    return draw


@router.get("/{draw_no}", response_model=DrawOut)
def get_draw(draw_no: int, db: Session = Depends(get_db)) -> Draw:
    if not (1 <= draw_no <= 32767):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 회차입니다."
        )
    draw = db.get(Draw, draw_no)
    if draw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 회차입니다."
        )
    return draw
