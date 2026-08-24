from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.assignment import Assignment, WeeklyCycle
from app.models.combination import CombinationPool
from app.models.draw import Draw, draw_date_for
from app.models.member import Member
from app.schemas.assignment import WeeklyCycleLinkDrawIn, WeeklyCycleOut
from app.schemas.draw import DrawIn, DrawOut
from app.services import push_service, week_service, winchecker

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_api_key: str = Header(...)) -> None:
    if x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="관리자 인증이 필요합니다."
        )


@router.post(
    "/weekly-cycles/rollover",
    dependencies=[Depends(_require_admin)],
    description=(
        "주간 리셋을 수동으로 트리거한다. 정확한 컷오버 시각이 아직 미확정이므로, "
        "스케줄러(app/jobs/scheduler.py)가 잘못 설정되었거나 지연될 때의 폴백으로 쓴다."
    ),
)
def trigger_rollover(db: Session = Depends(get_db)) -> dict:
    cycle = week_service.rollover(db)
    return {
        "id": cycle.id,
        "cycle_key": cycle.cycle_key.isoformat(),
        "starts_at": cycle.starts_at.isoformat(),
    }


@router.post(
    "/draws",
    response_model=DrawOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_require_admin)],
    description=(
        "당첨번호를 수동으로 입력한다. 동행복권 사이트가 자동 요청을 차단(302 리다이렉트)할 "
        "때 우회를 시도하지 않고, 관리자가 직접 입력하는 대체 경로로 쓴다. 이미 등록된 "
        "회차면 409를 반환한다."
    ),
)
def create_draw(payload: DrawIn, db: Session = Depends(get_db)) -> Draw:
    if db.get(Draw, payload.draw_no) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{payload.draw_no}회는 이미 등록되어 있습니다.",
        )

    numbers = sorted(payload.numbers)
    draw = Draw(
        draw_no=payload.draw_no,
        n1=numbers[0],
        n2=numbers[1],
        n3=numbers[2],
        n4=numbers[3],
        n5=numbers[4],
        n6=numbers[5],
        bonus_no=payload.bonus_no,
        draw_date=payload.draw_date or draw_date_for(payload.draw_no),
        source="manual",
    )
    db.add(draw)
    db.commit()
    db.refresh(draw)

    cycle = week_service.find_cycle_for_draw_date(db, draw.draw_date)
    if cycle is not None:
        cycle.associated_draw_no = draw.draw_no
        db.commit()

    return draw


@router.get(
    "/weekly-cycles",
    response_model=list[WeeklyCycleOut],
    dependencies=[Depends(_require_admin)],
    description="주차 목록을 최신순으로 조회한다. 당첨번호를 어느 주차에 연결할지 확인할 때 쓴다.",
)
def list_weekly_cycles(
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[WeeklyCycle]:
    return db.query(WeeklyCycle).order_by(desc(WeeklyCycle.starts_at)).limit(limit).all()


@router.post(
    "/weekly-cycles/{cycle_id}/link-draw",
    response_model=WeeklyCycleOut,
    dependencies=[Depends(_require_admin)],
    description=(
        "특정 주차에 당첨 회차를 연결한다. 이 연결이 있어야 회원이 "
        "GET /me/assignments/win-check로 해당 주차의 당첨 여부를 확인할 수 있다."
    ),
)
def link_draw_to_cycle(
    cycle_id: int, payload: WeeklyCycleLinkDrawIn, db: Session = Depends(get_db)
) -> WeeklyCycle:
    cycle = db.get(WeeklyCycle, cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 주차입니다."
        )
    draw = db.get(Draw, payload.draw_no)
    if draw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{payload.draw_no}회는 등록되어 있지 않습니다. 먼저 POST /admin/draws로 등록하세요.",
        )
    cycle.associated_draw_no = payload.draw_no
    db.commit()
    db.refresh(cycle)
    return cycle


@router.post(
    "/weekly-cycles/{cycle_id}/notify-winners",
    dependencies=[Depends(_require_admin)],
    description=(
        "해당 주차에 배정된 조합을 당첨번호와 비교해 당첨된 회원에게 웹 푸시 알림을 "
        "보낸다. 당첨번호 등록/연결 시 자동으로 호출되지 않으며, 관리자가 필요할 때 "
        "직접 호출해야 한다(웹 푸시 채널만 구현됨 — 카카오톡 알림 등은 추후 추가 예정)."
    ),
)
def notify_winners(cycle_id: int, db: Session = Depends(get_db)) -> dict:
    cycle = db.get(WeeklyCycle, cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 주차입니다."
        )
    if cycle.associated_draw_no is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이 주차에 연결된 당첨번호가 없습니다. 먼저 link-draw로 연결하세요.",
        )
    draw = db.get(Draw, cycle.associated_draw_no)

    assignments = db.query(Assignment).filter(Assignment.weekly_cycle_id == cycle.id).all()
    if not assignments:
        return {"notified_members": 0, "winning_combinations": 0}

    combo_ids = [a.combination_id for a in assignments]
    numbers_map = {
        row.id: sorted(row.numbers)
        for row in db.query(CombinationPool).filter(CombinationPool.id.in_(combo_ids)).all()
    }

    ranks_by_member: dict[int, list[int]] = {}
    for a in assignments:
        result = winchecker.check(
            a.combination_id, numbers_map[a.combination_id], draw.numbers, draw.bonus_no
        )
        if result.rank is not None:
            ranks_by_member.setdefault(a.member_id, []).append(result.rank)

    notified = 0
    for member_id, ranks in ranks_by_member.items():
        member = db.get(Member, member_id)
        if member is None:
            continue
        push_service.notify_win(
            db, member, draw.draw_no, best_rank=min(ranks), win_count=len(ranks)
        )
        notified += 1

    return {
        "notified_members": notified,
        "winning_combinations": sum(len(r) for r in ranks_by_member.values()),
    }
