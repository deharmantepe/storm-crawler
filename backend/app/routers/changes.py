from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Regulation, RegulationVersion

router = APIRouter()


@router.get("/updated")
def updated_regulations(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Regulation)
        .where(Regulation.version > 1)
        .order_by(Regulation.last_seen_at.desc())
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    return [
        {
            "id": row.id,
            "title": row.title,
            "url": row.url,
            "version": row.version,
            "last_seen_at": row.last_seen_at,
        }
        for row in rows
    ]


@router.get("/{regulation_id}/versions")
def regulation_versions(regulation_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(RegulationVersion)
        .where(RegulationVersion.regulation_id == regulation_id)
        .order_by(RegulationVersion.version.desc())
    )
    versions = list(db.scalars(stmt).all())
    return [
        {
            "version": row.version,
            "content_hash": row.content_hash,
            "summary": row.summary,
            "created_at": row.created_at,
        }
        for row in versions
    ]
