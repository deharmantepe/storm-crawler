from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

app = FastAPI(title="Render Service", version="0.1.0")


class RenderRequest(BaseModel):
    url: HttpUrl
    wait_until: str = "networkidle"
    timeout_ms: int = 45000


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/render")
async def render_page(req: RenderRequest) -> dict[str, str]:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            await page.goto(str(req.url), wait_until=req.wait_until, timeout=req.timeout_ms)
            html = await page.content()
            final_url = page.url
            await context.close()
            await browser.close()
        return {"url": str(req.url), "final_url": final_url, "html": html}
    except PlaywrightTimeoutError as exc:
        raise HTTPException(status_code=504, detail=f"Render timeout: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Render failed: {exc}") from exc
