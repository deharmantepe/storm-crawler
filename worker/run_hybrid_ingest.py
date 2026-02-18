from pathlib import Path

from app.config import settings
from app.db import SessionLocal, init_db
from app.services.scrape_pipeline import RegulationScrapePipeline

DEFAULT_SEEDS = [
    "https://www.mevzuat.gov.tr/",
]


def load_storm_urls() -> list[str]:
    path = Path(settings.storm_discovered_urls_file)
    if not path.exists():
        return []
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        normalized = line.strip()
        if normalized and normalized.startswith("http"):
            urls.append(normalized)
    return list(dict.fromkeys(urls))


def main() -> None:
    init_db()
    storm_urls = load_storm_urls()

    with SessionLocal() as db:
        pipeline = RegulationScrapePipeline(db)
        result = pipeline.run(seed_urls=DEFAULT_SEEDS, extra_urls=storm_urls)
    print({"storm_urls": len(storm_urls), **result})


if __name__ == "__main__":
    main()
