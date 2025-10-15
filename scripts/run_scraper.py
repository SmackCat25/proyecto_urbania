# Productos para Web Scraping
from amazon_scraper.scraper import scrape_url
from amazon_scraper.writer import write_to_csv

URLS = [
    "https://www.amazon.com/-/es/MSI-Escritorio-para-juegos-Codex/dp/B0F15TM77B/",
    "https://www.amazon.com/-/es/CyberPowerPC-i7-14700F-GeForce-Windows-GXiVR8040A17/dp/B0DW48GN42/",
    "https://www.amazon.com/-/es/Xbox-Wireless-Gaming-Controller-Consola-juegos/dp/B0F1HX3WXX/",
    "https://www.amazon.com/-/es/Logitech-305-LIGHTSPEED-inalámbrico-programables/dp/B07CMS5Q6P/",
    "https://www.amazon.com/Portátil-computadora-procesador-generación-retroiluminado/dp/B0CGRTXH96/"
]

if __name__ == "__main__":
    products = []
    for url in URLS:
        data = scrape_url(url)
        if data:
            products.append(data)
            write_to_csv(products)

    print("El web scraping ha finalizado.")