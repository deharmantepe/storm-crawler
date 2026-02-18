# StormCrawler Entegrasyonu

Bu klasör StormCrawler için başlangıç konfigürasyonlarını içerir.

## Amaç
- Büyük ölçek URL keşfi ve frontier yönetimi
- Keşfedilen URL listesini `output/discovered_urls.txt` dosyasına aktarma
- Sonrasında backend pipeline ile içerik işleme

## Çalışma modeli
1. StormCrawler topology URL keşfi yapar.
2. Keşfedilen URL'ler `output/discovered_urls.txt` dosyasına yazılır.
3. `worker/run_hybrid_ingest.py` bu URL'leri okuyup Playwright+Trafilatura pipeline'ında işler.

## Not
Bu repoda Storm cluster kurulumuna ait tam topology jar üretimi yerine entegrasyon iskeleti verilir.
Üretimde Apache Storm + StormCrawler topology deploy edilerek bu dosya çıkışı beslenir.
