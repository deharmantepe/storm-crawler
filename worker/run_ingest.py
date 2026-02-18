from app.db import SessionLocal, init_db
from app.services.scrape_pipeline import RegulationScrapePipeline

DEFAULT_SEEDS = [
    "https://www.mevzuat.gov.tr/",
]


def main() -> None:
    init_db()
    with SessionLocal() as db:
        pipeline = RegulationScrapePipeline(db)
        result = pipeline.run(DEFAULT_SEEDS)
    print(result)


if __name__ == "__main__":
    main()
