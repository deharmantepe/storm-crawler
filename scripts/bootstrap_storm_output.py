from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

SEEDS = ["https://www.mevzuat.gov.tr/"]
OUT = Path("data/stormcrawler/discovered_urls.txt")


def main() -> None:
    client = httpx.Client(timeout=20, follow_redirects=True)
    discovered: set[str] = set()

    for seed in SEEDS:
        try:
            response = client.get(seed)
            response.raise_for_status()
        except httpx.HTTPError:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("a[href]"):
            url = urljoin(seed, anchor.get("href", "")).split("#")[0]
            if url.startswith("http"):
                discovered.add(url)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(sorted(discovered)), encoding="utf-8")
    print({"written": len(discovered), "file": str(OUT)})


if __name__ == "__main__":
    main()
