import csv, os
from urbania_scraper.config import OUTPUT_FILE_NAME

COLUMNS = [
    "url","titulo","ubicacion_raw",
    "precio_soles","precio_usd",
    "m2_total","m2_techada",
    "dormitorios","banos","estacionamientos",
    "antiguedad_anios","descripcion_snippet",
    "precio_soles_x_m2"
]

def write_csv(data, out_path: str | None = None):
    path = out_path or OUTPUT_FILE_NAME
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for row in data:
            # Aseguramos todas las claves
            w.writerow({c: row.get(c) for c in COLUMNS})
    return path
