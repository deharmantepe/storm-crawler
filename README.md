# Regülasyon Bilgi Platformu (Hibrit Mimari)

Bu proje, StormCrawler + Playwright render + Trafilatura/Unstructured hattıyla regülasyon verisini toplayan, temizleyen, versiyonlayan ve API ile sunan temel bir platformdur.

## 1) Bu kurulumla neler yapabilirsin?
- Büyük URL keşfi (StormCrawler entegrasyonu)
- JS/dinamik sayfaları render ederek içerik alma (Playwright servis)
- Gürültüsüz metin/markdown çıkarımı (Trafilatura, fallback: Unstructured)
- Metadata ile indeksleme (tip, kurum, madde no)
- Değişiklik takibi ve versiyon geçmişi
- RAG için temiz veri üretimi

## 2) Mimari
- **Collector**: StormCrawler (output URL listesi)
- **Render**: `render-service` (Playwright FastAPI)
- **Extraction/Normalize**: backend `RegulationScrapePipeline`
- **Storage**: SQLite (`data/regulations.db`)
- **Serving**: FastAPI endpointleri

Akış:
1. StormCrawler URL keşfi yapar (`data/stormcrawler/discovered_urls.txt`)
2. Worker, bu URL'leri okuyup render+extract pipeline'a sokar
3. API arama, listeleme, değişiklik ve versiyon verisini sunar

## 3) Hızlı Başlangıç (Docker)
1. Ana servisler:
   - `docker compose up -d api render-service`
2. İsteğe bağlı Storm altyapısı:
   - `docker compose --profile storm up -d`
3. İlk URL listesi (demo):
   - `python scripts/bootstrap_storm_output.py`
4. Hibrit ingest:
   - `PYTHONPATH=backend python worker/run_hybrid_ingest.py`

## 4) Hızlı Başlangıç (Lokal)
1. `cd backend`
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. API: `uvicorn app.main:app --reload`
5. Hibrit ingest: `PYTHONPATH=backend python worker/run_hybrid_ingest.py`

## 5) API Endpointleri
- `GET /health`
- `GET /regulations?limit=50&offset=0`
- `GET /regulations/{id}`
- `GET /search?q=tebliğ`
- `GET /changes/updated`
- `GET /changes/{regulation_id}/versions`

## 6) StormCrawler notu
`stormcrawler/` klasöründe seed ve crawler config iskeleti vardır. Üretimde StormCrawler topology deploy edilerek URL frontier sürekli beslenir.

## 7) Uyum ve güvenlik
- Robots/kullanım şartlarına uyumlu crawl policy uygula
- Hız limiti ve retry kullan
- Canonical URL + hash deduplikasyonunu aktif tut

