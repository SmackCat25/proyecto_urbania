# Ejecutable: Urbania (solo San Miguel, Lima)
from datetime import datetime
from urbania_scraper.scraper import fetch_inmueble_urls_from_sitemaps, scrape_urbania_san_miguel
from urbania_scraper.writer import write_csv
from urbania_scraper.config import MAX_URLS

def main():
    print("[1/3] Descubriendo URLs desde sitemaps…")
    urls = fetch_inmueble_urls_from_sitemaps(max_urls=MAX_URLS)
    print(f"  -> URLs descubiertas: {len(urls)}")

    print("[2/3] Parseando fichas (filtrando San Miguel)…")
    rows, ok, skipped, errors = scrape_urbania_san_miguel(urls)
    print(f"  -> OK={ok} | Skip(no San Miguel)={skipped} | Errors={errors}")

    if not rows:
        print("No se obtuvieron fichas de San Miguel con las heurísticas actuales.")
        return

    print("[3/3] Exportando CSV…")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = write_csv(rows, out_path=f\"urbania_san_miguel_{ts}.csv\")
    print(f"Listo. CSV: {out}")

if __name__ == "__main__":
    main()
