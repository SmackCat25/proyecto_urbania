from playwright.sync_api import sync_playwright
import gzip, os, csv, requests
from bs4 import BeautifulSoup
from pathlib import Path

# DATA_DIR = r"C:\Users\maria\PycharmProjects\Urbania_Proyecto\Scrapping\data"
# DATA_URL = r"C:\Users\maria\PycharmProjects\Urbania_Proyecto\Scrapping"

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # sube dos niveles
DATA_DIR = BASE_DIR / "Scrapping" / "data"
DATA_URL = BASE_DIR / "Scrapping"
ROBOTS_URL = "https://urbania.pe/robots.txt"

def get_sitemaps_from_robots():
    """Lee robots.txt y devuelve todos los sitemaps declarados"""
    text = requests.get(ROBOTS_URL).text
    sitemaps = [line.split(": ", 1)[1] for line in text.splitlines() if line.lower().startswith("sitemap:")]
    return sitemaps

def download_and_parse_all():
    all_urls = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context()
        page = context.new_page()

        # 1. Obtener todos los sitemaps desde robots.txt
        sitemap_indices = get_sitemaps_from_robots()
        print(f"Encontrados {len(sitemap_indices)} sitemaps en robots.txt")
        for index_url in sitemap_indices:
            print(f"\nProcesando índice: {index_url}")

            # 2. Abrir cada índice
            response = page.goto(index_url)
            soup_index = BeautifulSoup(response.text(), "xml")

            # 3. Extraer todos los .gz de ese índice
            gz_links = [loc.text for loc in soup_index.find_all("loc") if loc.text.endswith(".xml.gz")]
            print(f"  → {len(gz_links)} archivos .gz encontrados")

            # 4. Descargar cada .gz
            for gz_link in gz_links:
                print("   Descargando:", gz_link)
                with page.expect_download() as download_info:
                    page.evaluate(f"window.location.href = '{gz_link}'")
                download = download_info.value

                # Guardar en carpeta data
                filename = os.path.join(DATA_DIR, download.suggested_filename)
                download.save_as(filename)
                print(f"   Archivo guardado en: {filename}")

                # 5. Descomprimir y parsear
                with gzip.open(filename, "rb") as f:
                    xml_content = f.read()
                soup = BeautifulSoup(xml_content, "xml")

                # 6. Extraer links internos
                urls = [loc.text for loc in soup.find_all("loc")]
                print(f"     → {len(urls)} links extraídos de {os.path.basename(filename)}")
                all_urls.extend(urls)

        browser.close()

    # 7. Guardar todos los URLs en un CSV único
    csv_path = os.path.join(DATA_URL, "urls.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url"])
        for u in sorted(set(all_urls)):  # deduplicamos
            writer.writerow([u])

    print(f"\n✅ Total de URLs recolectadas: {len(set(all_urls))}")
    print(f"📄 CSV guardado en: {csv_path}")

if __name__ == "__main__":
    download_and_parse_all()