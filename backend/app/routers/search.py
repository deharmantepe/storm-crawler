from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Regulation
from app.schemas import RegulationOut

router = APIRouter()


@router.get("", response_model=list[RegulationOut])
def search_regulations(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    pattern = f"%{q}%"
    stmt = (
        select(Regulation)
        .where(or_(Regulation.title.ilike(pattern), Regulation.content_text.ilike(pattern)))
        .order_by(Regulation.last_seen_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
