from bs4 import BeautifulSoup
from pathlib import Path
import csv
from playwright.sync_api import sync_playwright
import re
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_URL = BASE_DIR / "Scrapping"
OUTPUT_FILE_NAME = "inmuebles.csv"

# Cargar URLs del CSV
lista_urls = pd.read_csv(DATA_URL / "urls.csv", delimiter=';')
lista_urls = lista_urls[lista_urls['url'].str.contains("/inmueble/")]
print("Total de URLS: ", lista_urls.shape[0])

URLS = lista_urls['url'][:10].tolist()

# Cargar URLs ya scrapeadas para evitar duplicados
urls_scrapeadas = set()
output_file = DATA_URL / OUTPUT_FILE_NAME
if output_file.exists():
    try:
        df_existente = pd.read_csv(output_file, delimiter=';', encoding='latin-1') #
        urls_scrapeadas = set(df_existente['url'].tolist())
        print(f"Se encontraron {len(urls_scrapeadas)} URLs ya scrapeadas")
    except Exception as e:
        print(f"Error cargando CSV existente: {e}")

# Filtrar solo URLs nuevas
URLS = [url for url in URLS if url not in urls_scrapeadas]
print(f"URLs nuevas a scrapear: {len(URLS)}")


def clean_text(text):
    """Limpia espacios en blanco y saltos de línea innecesarios"""
    if not text:
        return None
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned if cleaned else None


def parse_product(soup: BeautifulSoup, url: str):
    product = {}

    try:
        title_tag = soup.select_one("h1.title-property")
        title_text = clean_text(title_tag.get_text()) if title_tag else None

        if not title_text:
            return None

        product["tipo_contrato"] = title_text.split()[0] if len(title_text.split()) > 0 else None
        product["tipo_vivienda"] = title_text.split()[1] if len(title_text.split()) > 1 else None

        match = re.search(r'S/ (.+)$', title_text)
        product["precio"] = match.group(1) if match else None

        direccion_tag = soup.select_one("div.section-location-property h4")
        if direccion_tag:
            direccion_completa = direccion_tag.get_text(strip=True)
            ultima_coma = direccion_completa.rfind(', ')
            product["distrito"] = direccion_completa[
                ultima_coma + 1:].strip() if ultima_coma != -1 else direccion_completa
            product["direccion"] = direccion_completa
        else:
            product["distrito"] = None
            product["direccion"] = None

        product["area_total"] = clean_text((area_total := soup.select_one("li:has(i.icon-stotal)")).get_text()) if (
            area_total := soup.select_one("li:has(i.icon-stotal)")) else None
        product["area_cubierta"] = clean_text(
            (area_cubierta := soup.select_one("li:has(i.icon-scubierta)")).get_text()) if (
            area_cubierta := soup.select_one("li:has(i.icon-scubierta)")) else None
        product["banos"] = clean_text((banos := soup.select_one("li:has(i.icon-bano)")).get_text()) if (
            banos := soup.select_one("li:has(i.icon-bano)")) else None
        product["cochera"] = clean_text((cochera := soup.select_one("li:has(i.icon-cochera)")).get_text()) if (
            cochera := soup.select_one("li:has(i.icon-cochera)")) else None
        product["dormitorio"] = clean_text((dormitorio := soup.select_one("li:has(i.icon-dormitorio)")).get_text()) if (
            dormitorio := soup.select_one("li:has(i.icon-dormitorio)")) else None
        product["antiguedad"] = clean_text((antiguedad := soup.select_one("li:has(i.icon-antiguedad)")).get_text()) if (
            antiguedad := soup.select_one("li:has(i.icon-antiguedad)")) else None

        product["url"] = url
        # product["isread"] = 1

        return product
    except Exception as e:
        print(f"Error parseando: {e}")
        return None


def scrape_url(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url, timeout=60000)

            page.wait_for_selector("h1.title-property", timeout=15000)
            page.wait_for_timeout(3000)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            browser.close()

            return parse_product(soup, url)
    except Exception as e:
        print(f"Error scrapeando {url}: {e}")
        return None


def append_to_csv(data):
    """Append datos al CSV existente en lugar de sobrescribir"""
    if not data:
        print("No hay datos disponibles.")
        return

    output_file = DATA_URL / OUTPUT_FILE_NAME
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = data[0].keys()

    # Si el archivo existe, append; si no, crea con headers
    file_exists = output_file.exists()

    with open(output_file, mode="a" if file_exists else "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)

    print(f"✅ {len(data)} registros guardados en: {output_file}")


if __name__ == "__main__":
    products = []

    for i, url in enumerate(URLS, 1):
        print(f"[{i}/{len(URLS)}] Scrapeando: {url}")
        data = scrape_url(url)

        if data:
            products.append(data)
            print(f"✅ Datos obtenidos correctamente\n")
        else:
            print(f"⚠️ No se obtuvieron datos para esta URL\n")

    if products:
        append_to_csv(products)
        print(f"✅ Scraping finalizado. Se scrapearon {len(products)}/{len(URLS)} URLs nuevas.")
    else:
        print("❌ No se obtuvieron datos de ninguna URL.")