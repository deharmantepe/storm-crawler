from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routers import changes, ops, regulations, search

app = FastAPI(
    title="Regülasyon Bilgi Platformu API",
    version="0.1.0",
    description="Regülasyon toplama, depolama ve arama API'si",
)

static_dir = "app/static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(f"{static_dir}/index.html")


app.include_router(regulations.router, prefix="/regulations", tags=["regulations"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(changes.router, prefix="/changes", tags=["changes"])
app.include_router(ops.router, prefix="/ops", tags=["ops"])
