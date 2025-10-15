from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
import re

# ----------------- Configuración del navegador -----------------
options = Options()
options.add_argument("--headless")        # quita esta línea si quieres ver la ventana
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36 (CursoDataMining/1.0)"
)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                          options=options)

url = "https://urbania.pe/inmueble/proyecto/ememefin-proyecto-edificios-en-aurora-miraflores-aurora-taller-de-diseno-constructivo-sac-146976422"
driver.get(url)

# Esperas básicas a que carguen bloques clave
wait = WebDriverWait(driver, 15)
wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.price-operation-type")))
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.section-location-property")))

# HTML renderizado (post Cloudflare)
html = driver.page_source
driver.quit()

# ----------------- Parse con BeautifulSoup -----------------
soup = BeautifulSoup(html, "html.parser")
resultados = []

# 1) OPERACIONES: venta / alquiler (y su monto) en <div class="price-operation-type ...">
for bloque in soup.select("div.price-operation-type"):
    # tipo de operación: <span class="operation-type">venta</span> o "alquiler"
    tipo_tag = bloque.select_one("span.operation-type")
    tipo = tipo_tag.get_text(strip=True).lower() if tipo_tag else ""

    # monto: dentro del mismo bloque hay varios <span>; tomamos el que tenga moneda/números
    monto = ""
    for sp in bloque.select("span"):
        txt = sp.get_text(" ", strip=True)
        if re.search(r"(S/|US\$|\d)", txt):
            # evitamos capturar la palabra "Desde" sola
            if not re.match(r"(?i)desde$", txt):
                monto = txt
    if tipo:
        resultados.append({"campo": f"operacion_{tipo}", "valor": monto or "N/D"})

# 2) UBICACIÓN: <div class="section-location-property"><h4>...</h4></div>
loc = soup.select_one("div.section-location-property h4")
if loc:
    resultados.append({"campo": "ubicacion", "valor": loc.get_text(" ", strip=True)})

# 3) DESCRIPCIÓN: la clase suele empezar con "description-module__wrapper-description"
desc = soup.select_one('div[class^="description-module__wrapper-description"]')
if desc:
    resultados.append({"campo": "descripcion", "valor": desc.get_text(" ", strip=True)})

# 4) (Opcional) Otras etiquetas útiles: <div class="label"> (m², dorms, baños, unidades)
for lab in soup.select("div.label"):
    txt = lab.get_text(" ", strip=True)
    if not txt:
        continue
    # Clasificación rápida por palabra clave
    if "Unidad" in txt:
        resultados.append({"campo": "unidades", "valor": txt})
    elif "m²" in txt and "techada" in txt:
        resultados.append({"campo": "m2_techada", "valor": txt})
    elif "m²" in txt:
        resultados.append({"campo": "m2_total", "valor": txt})
    elif re.search(r"(?i)dorm", txt):
        resultados.append({"campo": "dormitorios", "valor": txt})
    elif re.search(r"(?i)bañ", txt):
        resultados.append({"campo": "banos", "valor": txt})
    else:
        resultados.append({"campo": "label_otro", "valor": txt})

# --------- Mostrar resultados en el formato pedido ---------
for r in resultados:
    print(f"{r['campo']}: {r['valor']}")

