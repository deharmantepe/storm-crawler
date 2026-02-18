from __future__ import annotations

import difflib
import hashlib
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Regulation, RegulationVersion


class RegulationScrapePipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.client = httpx.Client(
            headers={"User-Agent": settings.user_agent},
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
        )

    def run(self, seed_urls: list[str], extra_urls: list[str] | None = None) -> dict[str, int]:
        Path(settings.raw_output_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.processed_output_dir).mkdir(parents=True, exist_ok=True)

        discovered = self._discover_links(seed_urls)
        if extra_urls:
            discovered = sorted(set(discovered).union(set(extra_urls)))

        processed = 0
        upserted = 0
        changed = 0

        for url in discovered[: settings.max_pages_per_run]:
            html = self._download_html(url)
            if not html:
                continue

            extracted = self._extract_markdown(html)
            if not extracted:
                continue

            title = self._extract_title(html) or url
            plain_text = re.sub(r"\s+", " ", extracted).strip()
            content_hash = hashlib.sha256(plain_text.encode("utf-8")).hexdigest()
            metadata = self._extract_metadata(title=title, url=url, plain_text=plain_text)
            canonical_url = self._canonicalize_url(url)

            has_changed = self._upsert_regulation(
                title=title,
                url=url,
                canonical_url=canonical_url,
                source=urlparse(url).netloc,
                instrument_type=metadata["instrument_type"],
                institution=metadata["institution"],
                article_no=metadata["article_no"],
                content_markdown=extracted,
                content_text=plain_text,
                content_hash=content_hash,
            )

            self._write_processed(url, extracted)
            processed += 1
            upserted += 1
            changed += int(has_changed)
            time.sleep(settings.request_delay_seconds)

        self.db.commit()
        return {
            "discovered": len(discovered),
            "processed": processed,
            "upserted": upserted,
            "changed": changed,
        }

    def _discover_links(self, seed_urls: list[str]) -> list[str]:
        links: set[str] = set()
        for seed in seed_urls:
            html = self._safe_get(seed)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.select("a[href]"):
                absolute = urljoin(seed, a.get("href", ""))
                if absolute.startswith("http"):
                    links.add(absolute.split("#")[0])
        return sorted(links)

    def _extract_title(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else None

    def _download_html(self, url: str) -> str | None:
        if settings.use_playwright_render and self._needs_browser_render(url):
            rendered = self._fetch_with_render_service(url)
            if rendered:
                return rendered
        return self._safe_get(url)

    def _needs_browser_render(self, url: str) -> bool:
        lowered = url.lower()
        dynamic_hints = ["#/", "?page=", "arama", "search", "query", "spa"]
        return any(hint in lowered for hint in dynamic_hints)

    def _fetch_with_render_service(self, url: str) -> str | None:
        try:
            response = self.client.post(
                settings.render_service_url,
                json={"url": url, "wait_until": "networkidle", "timeout_ms": settings.render_timeout_seconds * 1000},
                timeout=settings.render_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("html")
        except (httpx.HTTPError, ValueError):
            return None

    def _safe_get(self, url: str) -> str | None:
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError:
            return None

    def _extract_markdown(self, html: str) -> str | None:
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_formatting=True,
            output_format="markdown",
        )
        if extracted:
            return extracted
        if not settings.use_unstructured_fallback:
            return None
        return self._extract_with_unstructured(html)

    def _extract_with_unstructured(self, html: str) -> str | None:
        try:
            from unstructured.partition.html import partition_html
        except Exception:
            return None

        try:
            elements = partition_html(text=html)
            lines = [str(element).strip() for element in elements if str(element).strip()]
            if not lines:
                return None
            return "\n\n".join(lines)
        except Exception:
            return None

    def _canonicalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def _extract_metadata(self, *, title: str, url: str, plain_text: str) -> dict[str, str | None]:
        lower = f"{title} {url} {plain_text[:2000]}".lower()

        instrument_type = None
        for keyword in ["kanun", "yönetmelik", "tebliğ", "genelge", "karar", "anayasa"]:
            if keyword in lower:
                instrument_type = keyword
                break

        institution = None
        for keyword in ["cumhurbaşkanlığı", "bakanlığı", "tbmm", "resmî gazete", "resmi gazete"]:
            if keyword in lower:
                institution = keyword
                break

        article_no = None
        article_match = re.search(r"madde\s*(\d+[/-]?\w*)", lower)
        if article_match:
            article_no = article_match.group(1)

        return {
            "instrument_type": instrument_type,
            "institution": institution,
            "article_no": article_no,
        }

    def _upsert_regulation(
        self,
        *,
        title: str,
        url: str,
        canonical_url: str,
        source: str,
        instrument_type: str | None,
        institution: str | None,
        article_no: str | None,
        content_markdown: str,
        content_text: str,
        content_hash: str,
    ) -> bool:
        stmt = select(Regulation).where(Regulation.url == url)
        existing = self.db.scalars(stmt).first()

        if existing:
            changed = existing.content_hash != content_hash
            if changed:
                existing.version += 1
                self._create_version_snapshot(existing.id, existing.version, content_hash, existing.content_text or "", content_text)
            existing.title = title
            existing.source = source
            existing.canonical_url = canonical_url
            existing.instrument_type = instrument_type
            existing.institution = institution
            existing.article_no = article_no
            existing.content_markdown = content_markdown
            existing.content_text = content_text
            existing.content_hash = content_hash
            existing.last_seen_at = datetime.utcnow()
            return changed

        row = Regulation(
            title=title,
            url=url,
            source=source,
            canonical_url=canonical_url,
            instrument_type=instrument_type,
            institution=institution,
            article_no=article_no,
            content_markdown=content_markdown,
            content_text=content_text,
            content_hash=content_hash,
            version=1,
            last_seen_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        self.db.add(row)
        self.db.flush()
        self._create_version_snapshot(row.id, 1, content_hash, "", content_text)
        return True

    def _create_version_snapshot(
        self,
        regulation_id: int,
        version: int,
        content_hash: str,
        previous_text: str,
        current_text: str,
    ) -> None:
        prev_lines = previous_text.splitlines()[:120]
        curr_lines = current_text.splitlines()[:120]
        diff = difflib.unified_diff(prev_lines, curr_lines, n=1)
        summary = " | ".join(list(diff)[:8])[:1000]
        snapshot = RegulationVersion(
            regulation_id=regulation_id,
            content_hash=content_hash,
            version=version,
            summary=summary or "İlk versiyon",
            created_at=datetime.utcnow(),
        )
        self.db.add(snapshot)

    def _write_processed(self, url: str, markdown: str) -> None:
        file_name = hashlib.md5(url.encode("utf-8")).hexdigest() + ".md"
        file_path = Path(settings.processed_output_dir) / file_name
        file_path.write_text(markdown, encoding="utf-8")
