from bs4 import BeautifulSoup
from pathlib import Path
import csv
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_URL = BASE_DIR / "Scrapping"
OUTPUT_FILE_NAME = "inmuebles_maria.csv"

# Cargar y filtrar URLs
lista_urls = pd.read_csv(DATA_URL / "urls.csv", delimiter=';')
lista_urls = lista_urls[lista_urls['url'].str.contains("/inmueble/")&lista_urls['url'].str.contains("-alquiler-")]
print(f"Total de URLs encontradas: {lista_urls.shape[0]}")

URLS = lista_urls['url'][550:600].tolist()

# Cargar URLs ya scrapeadas
urls_scrapeadas = set()
output_file = DATA_URL / OUTPUT_FILE_NAME
if output_file.exists():
    try:
        df_existente = pd.read_csv(output_file, delimiter=';', encoding='latin-1')
        urls_scrapeadas = set(df_existente['url'].tolist())
        print(f"URLs ya scrapeadas: {len(urls_scrapeadas)}")
    except Exception as e:
        print(f"Error cargando CSV: {e}")

URLS = [url for url in URLS if url not in urls_scrapeadas]
print(f"URLs nuevas a scrapear: {len(URLS)}\n")


def clean_text(text):
    """Limpia espacios en blanco, saltos de línea y emojis"""
    if not text:
        return None
    # Remover solo emojis
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)  # Emojis
    text = re.sub(r'[\u2600-\u26FF]', '', text)  # Símbolos diversos
    text = re.sub(r'[\uFE00-\uFE0F]', '', text)  # Selectores de variación (causa del error)
    # Limpiar espacios múltiples
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned if cleaned else None


def get_driver():
    """Configura y retorna un driver de Selenium optimizado"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    )

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def parse_product(soup: BeautifulSoup, url: str):
    """Extrae información del inmueble desde el HTML parseado"""
    product = {}

    try:
        # Título y datos básicos
        title_tag = soup.select_one("h1.title-property")
        title_text = clean_text(title_tag.get_text()) if title_tag else None

        if not title_text:
            return None

        parts = title_text.split()
        product["tipo_contrato"] = parts[0] if len(parts) > 0 else None
        product["tipo_vivienda"] = parts[1] if len(parts) > 1 else None

        # Precio
        match = re.search(r'S/ (.+)$', title_text)
        product["precio"] = match.group(1) if match else None

        # Dirección y distrito
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

        # Características del inmueble
        caracteristicas = {
            "area_total": "li:has(i.icon-stotal)",
            "area_cubierta": "li:has(i.icon-scubierta)",
            "banos": "li:has(i.icon-bano)",
            "medios_banos": "li:has(i.icon-toilete)",
            "cochera": "li:has(i.icon-cochera)",
            "dormitorio": "li:has(i.icon-dormitorio)",
            "antiguedad": "li:has(i.icon-antiguedad)"
        }

        for key, selector in caracteristicas.items():
            element = soup.select_one(selector)
            product[key] = clean_text(element.get_text()) if element else None

        descripcion = soup.select_one('div[class*="description-module__wrapper-description"]')
        product["descripcion"] = descripcion.get_text(separator='\n', strip=True) if descripcion else None

        product["url"] = url
        product["fecha_extraccion"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return product

    except Exception as e:
        print(f"  ⚠️ Error parseando contenido: {e}")
        return None


def scrape_url(url):
    """Scrapea una URL usando Selenium"""
    driver = None
    try:
        driver = get_driver()
        driver.get(url)

        # Esperar elemento clave
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.title-property")))

        # HTML renderizado
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        return parse_product(soup, url)

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def append_to_csv(data):
    """Guarda datos al CSV"""
    if not data:
        return

    output_file = DATA_URL / OUTPUT_FILE_NAME
    output_file.parent.mkdir(parents=True, exist_ok=True)

    file_exists = output_file.exists()

    with open(output_file, mode="a" if file_exists else "w", newline="", encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=';')
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)

    print(f"\n✅ {len(data)} registros guardados en: {output_file}")


if __name__ == "__main__":
    if not URLS:
        print("❌ No hay URLs nuevas para scrapear.")
        exit()

    products = []

    for i, url in enumerate(URLS, 1):
        print(f"[{i}/{len(URLS)}] Scrapeando...")
        data = scrape_url(url)

        if data:
            products.append(data)
            print(f"  ✅ Éxito: {data.get('tipo_vivienda', 'N/A')} en {data.get('distrito', 'N/A')}")
        else:
            print(f"  ⚠️ Sin datos")

    if products:
        append_to_csv(products)
        print(f"\n🎉 Scraping finalizado: {len(products)}/{len(URLS)} URLs procesadas.")
    else:
        print("\n❌ No se obtuvieron datos.")