import re
from bs4 import BeautifulSoup

SAN_MIGUEL_RX = re.compile(r"\bSan\s+Miguel\b", re.I)

def _clean(s: str) -> str:
    import re
    return re.sub(r"\s+", " ", s or "").strip()

def _to_float(x):
    if not x:
        return None
    s = x.strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    import re
    s = re.sub(r"[^\d.\-]", "", s)
    try:
        return float(s)
    except Exception:
        return None

def is_san_miguel(text: str) -> bool:
    return SAN_MIGUEL_RX.search(text or "") is not None

def parse_property_html(url: str, html: str) -> dict | None:
    """
    Parsea una ficha de Urbania y retorna dict con campos clave.
    Si no detecta 'San Miguel' en el contenido, retorna None.
    """
    soup = BeautifulSoup(html, "html.parser")
    text_all = soup.get_text(" ", strip=True)

    if not is_san_miguel(text_all):
        return None

    data = {"url": url}
    h1 = soup.select_one("h1") or soup.select_one("h2")
    data["titulo"] = _clean(h1.get_text()) if h1 else None

    # Precio en S/ y USD
    precio_sol = re.search(r"(?:S/|S\.\/)\s*([\d\.\,]+)", text_all, re.I)
    precio_usd = re.search(r"\bUSD\s*([\d\.\,]+)", text_all, re.I)
    data["precio_soles"] = _to_float(precio_sol.group(1)) if precio_sol else None
    data["precio_usd"] = _to_float(precio_usd.group(1)) if precio_usd else None

    # Specs
    specs_text = " ".join(el.get_text(" ", strip=True) for el in soup.select("li, .chip, .feature, .spec, .card, .characteristics, [class*='MuiGrid']"))
    big = f"{text_all} {specs_text}"

    m2_total = re.search(r"(\d{1,4}(?:[\.\,]\d{3})*(?:[\.\,]\d+)?)\s*m²\s*(?:tot|total|ocup|área ocupada)?", big, re.I)
    m2_tech = re.search(r"(\d{1,4}(?:[\.\,]\d{3})*(?:[\.\,]\d+)?)\s*m²\s*(?:cub|tech|constr|techada|construida)", big, re.I)
    data["m2_total"] = _to_float(m2_total.group(1)) if m2_total else None
    data["m2_techada"] = _to_float(m2_tech.group(1)) if m2_tech else None

    dorm = re.search(r"(\d+)\s*(?:dorm|dormitorio|habitaciones|hab)", big, re.I)
    ban = re.search(r"(\d+)\s*(?:bañ|baños|banos)", big, re.I)
    est = re.search(r"(\d+)\s*(?:estac|coch|cochera|estacionamiento)", big, re.I)
    antig = re.search(r"(\d+)\s*(?:año|años)\s*(?:de)?\s*(?:antig|antigüedad)", big, re.I)

    data["dormitorios"] = int(dorm.group(1)) if dorm else None
    data["banos"] = int(ban.group(1)) if ban else None
    data["estacionamientos"] = int(est.group(1)) if est else None
    data["antiguedad_anios"] = int(ig) if (ig := (antig.group(1) if antig else None)) else None

    # Ubicación raw
    breadcrumbs = " ".join(el.get_text(" ", strip=True) for el in soup.select("nav.breadcrumb, .breadcrumb, [aria-label='breadcrumb']"))
    if "San Miguel" in breadcrumbs:
        data["ubicacion_raw"] = _clean(breadcrumbs)
    else:
        mubi = re.search(r"([A-Za-zÁÉÍÓÚÜÑ\s\-]+,\s*San\s+Miguel,\s*Lima)", text_all, re.I)
        data["ubicacion_raw"] = _clean(mubi.group(1)) if mubi else "San Miguel, Lima"

    # Descripción (snippet)
    desc = None
    for lbl in soup.find_all(string=re.compile(r"Descripci[oó]n|Caracter[ií]sticas|Detalles", re.I)):
        try:
            desc = lbl.parent.get_text(" ", strip=True)
            break
        except Exception:
            pass
    if not desc:
        p = soup.select_one("p")
        desc = p.get_text(" ", strip=True) if p else None
    data["descripcion_snippet"] = _clean(desc)[:800] if desc else None

    # KPI
    if data["precio_soles"] and data["m2_total"] and data["m2_total"] > 0:
        data["precio_soles_x_m2"] = round(data["precio_soles"]/data["m2_total"], 2)
    else:
        data["precio_soles_x_m2"] = None

    return data
