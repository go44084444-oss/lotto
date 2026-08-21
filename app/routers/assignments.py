from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_member
from app.db.session import get_db
from app.models.assignment import Assignment, WeeklyCycle
from app.models.combination import CombinationPool
from app.models.draw import Draw
from app.models.member import Member, MembershipTier
from app.schemas.assignment import (
    AssignmentBatchOut,
    CombinationOut,
    WinCheckResponse,
    WinCheckResultItem,
)
from app.services import assignment_service, week_service, winchecker

router = APIRouter(prefix="/me/assignments", tags=["assignments"])


def _combo_numbers_map(db: Session, combo_ids: list[int]) -> dict[int, list[int]]:
    if not combo_ids:
        return {}
    rows = db.query(CombinationPool).filter(CombinationPool.id.in_(combo_ids)).all()
    return {row.id: sorted(row.numbers) for row in rows}


def _to_batch_out(
    db: Session, cycle: WeeklyCycle, quota: int, assignments: list[Assignment]
) -> AssignmentBatchOut:
    combo_ids = [a.combination_id for a in assignments]
    numbers_map = _combo_numbers_map(db, combo_ids)
    return AssignmentBatchOut(
        weekly_cycle_id=cycle.id,
        cycle_key=cycle.cycle_key,
        quota=quota,
        combinations=[CombinationOut(id=cid, numbers=numbers_map[cid]) for cid in combo_ids],
    )


@router.post(
    "",
    response_model=AssignmentBatchOut,
    description=(
        "이번 주 조합을 배정 요청한다. 이미 이번 주 배정이 있으면 동일한 결과를 그대로 "
        "반환한다(멱등). 배정된 조합은 확률을 높이지 않으며 단지 패턴이 뚜렷한 조합을 "
        "제외한 풀에서 무작위로 고른 것이다."
    ),
)
def request_assignment(
    response: Response,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> AssignmentBatchOut:
    cycle_before = week_service.get_or_create_current_cycle(db)
    already_assigned = (
        db.query(Assignment)
        .filter(Assignment.weekly_cycle_id == cycle_before.id, Assignment.member_id == member.id)
        .first()
        is not None
    )

    try:
        assignments = assignment_service.assign_for_member(db, member)
    except assignment_service.MemberWithdrawnError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="탈퇴한 회원은 조합을 배정받을 수 없습니다.",
        ) from exc
    except assignment_service.InsufficientPoolError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="배정 가능한 조합이 부족합니다. 잠시 후 다시 시도해주세요.",
        ) from exc

    response.status_code = (
        status.HTTP_200_OK if already_assigned else status.HTTP_201_CREATED
    )

    cycle = db.get(WeeklyCycle, assignments[0].weekly_cycle_id)
    tier = db.get(MembershipTier, member.tier)
    return _to_batch_out(db, cycle, tier.weekly_quota, assignments)


@router.get("/current", response_model=AssignmentBatchOut)
def get_current_assignment(
    member: Member = Depends(get_current_member), db: Session = Depends(get_db)
) -> AssignmentBatchOut:
    cycle = week_service.get_or_create_current_cycle(db)
    assignments = (
        db.query(Assignment)
        .filter(Assignment.weekly_cycle_id == cycle.id, Assignment.member_id == member.id)
        .all()
    )
    tier = db.get(MembershipTier, member.tier)
    return _to_batch_out(db, cycle, tier.weekly_quota, assignments)


@router.get("", response_model=AssignmentBatchOut)
def get_assignment_by_cycle(
    cycle_key: date = Query(...),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> AssignmentBatchOut:
    cycle = db.query(WeeklyCycle).filter(WeeklyCycle.cycle_key == cycle_key).first()
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 주차입니다."
        )
    assignments = (
        db.query(Assignment)
        .filter(Assignment.weekly_cycle_id == cycle.id, Assignment.member_id == member.id)
        .all()
    )
    tier = db.get(MembershipTier, member.tier)
    return _to_batch_out(db, cycle, tier.weekly_quota, assignments)


@router.get("/win-check", response_model=WinCheckResponse)
def win_check(
    cycle_key: date | None = Query(None),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> WinCheckResponse:
    if cycle_key is not None:
        cycle = db.query(WeeklyCycle).filter(WeeklyCycle.cycle_key == cycle_key).first()
        if cycle is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 주차입니다."
            )
    else:
        cycle = (
            db.query(WeeklyCycle)
            .filter(WeeklyCycle.associated_draw_no.isnot(None))
            .order_by(WeeklyCycle.starts_at.desc())
            .first()
        )
        if cycle is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="당첨 결과가 연결된 주차가 아직 없습니다.",
            )

    if cycle.associated_draw_no is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 주차의 당첨 결과가 아직 반영되지 않았습니다.",
        )

    draw = db.get(Draw, cycle.associated_draw_no)

    assignments = (
        db.query(Assignment)
        .filter(Assignment.weekly_cycle_id == cycle.id, Assignment.member_id == member.id)
        .all()
    )
    combo_ids = [a.combination_id for a in assignments]
    numbers_map = _combo_numbers_map(db, combo_ids)

    results = []
    for cid in combo_ids:
        r = winchecker.check(cid, numbers_map[cid], draw.numbers, draw.bonus_no)
        results.append(
            WinCheckResultItem(
                combination_id=r.combination_id,
                numbers=r.numbers,
                match_count=r.match_count,
                matched_bonus=r.matched_bonus,
                rank=r.rank,
            )
        )

    return WinCheckResponse(
        cycle_key=cycle.cycle_key,
        draw_no=draw.draw_no,
        winning_numbers=draw.numbers,
        bonus_no=draw.bonus_no,
        results=results,
    )
