from pathlib import Path

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.config import settings
from app.db import SessionLocal
from app.models import Regulation
from app.services.scrape_pipeline import RegulationScrapePipeline

router = APIRouter()


@router.get("/stats")
def stats() -> dict[str, int | bool]:
    with SessionLocal() as db:
        total = db.scalar(select(func.count(Regulation.id))) or 0
        updated = db.scalar(select(func.count(Regulation.id)).where(Regulation.version > 1)) or 0
    storm_count = 0
    storm_path = Path(settings.storm_discovered_urls_file)
    if storm_path.exists():
        storm_count = len([line for line in storm_path.read_text(encoding="utf-8").splitlines() if line.strip()])
    return {
        "total_regulations": int(total),
        "updated_regulations": int(updated),
        "storm_urls": int(storm_count),
        "render_enabled": bool(settings.use_playwright_render),
    }


@router.post("/ingest")
def run_ingest(seed: str = Query(default="https://www.mevzuat.gov.tr/")) -> dict[str, int]:
    extra: list[str] = []
    storm_file = Path(settings.storm_discovered_urls_file)
    if storm_file.exists():
        extra = [
            line.strip()
            for line in storm_file.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("http")
        ]

    with SessionLocal() as db:
        result = RegulationScrapePipeline(db).run(seed_urls=[seed], extra_urls=extra)
    return {"storm_urls": len(extra), **result}
