from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Regulation
from app.schemas import RegulationOut

router = APIRouter()


@router.get("", response_model=list[RegulationOut])
def list_regulations(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Regulation).order_by(Regulation.last_seen_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{regulation_id}", response_model=RegulationOut)
def get_regulation(regulation_id: int, db: Session = Depends(get_db)):
    row = db.get(Regulation, regulation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    return row
