from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Regülasyon Bilgi Platformu"
    user_agent: str = "RegulasyonPlatformBot/0.1 (+contact:admin@example.com)"
    request_timeout_seconds: int = 20
    request_delay_seconds: float = 1.0
    max_pages_per_run: int = 200
    use_playwright_render: bool = True
    render_service_url: str = "http://localhost:9000/render"
    render_timeout_seconds: int = 45
    use_unstructured_fallback: bool = True
    data_dir: str = str(Path(__file__).resolve().parents[1] / "data")
    storm_discovered_urls_file: str = str(Path(data_dir) / "stormcrawler" / "discovered_urls.txt")
    database_url: str = f"sqlite:///{(Path(data_dir) / 'regulations.db').as_posix()}"
    raw_output_dir: str = str(Path(data_dir) / "raw")
    processed_output_dir: str = str(Path(data_dir) / "processed")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
