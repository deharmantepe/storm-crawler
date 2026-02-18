from datetime import datetime

from pydantic import BaseModel


class RegulationOut(BaseModel):
    id: int
    title: str
    url: str
    canonical_url: str | None = None
    source: str
    instrument_type: str | None = None
    institution: str | None = None
    article_no: str | None = None
    version: int
    published_at: datetime | None = None
    last_seen_at: datetime

    class Config:
        from_attributes = True
