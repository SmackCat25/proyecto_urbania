# Configuración para scrapping académico de Urbania (solo San Miguel - Lima)
# Respeta robots.txt y usa el sitio sin sobrecargarlo.

HEADERS = {
    "User-Agent": "PUCP-AcademicScraper/1.0 (+mailto:tu-correo@pucp.edu.pe)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
}

# Delays conservadores
REQUEST_DELAY_SITEMAP = 2   # segundos entre lecturas de sitemap
REQUEST_DELAY_PAGE = 6      # segundos entre fichas

# Sitemaps principales del dominio (públicos)
SITEMAPS = [
    "https://urbania.pe/sitemaps_https.xml",
    "https://urbania.pe/sitemaps_list_emp_https.xml",
    "https://urbania.pe/sitemaps_prop_emp_https.xml",
]

# Límite de URLs a considerar (muestra académica)
MAX_URLS = 400

# Archivo de salida (CSV)
OUTPUT_FILE_NAME = "urbania_san_miguel.csv"
