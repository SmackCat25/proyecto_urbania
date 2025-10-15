import requests
from bs4 import BeautifulSoup
from .parser import parse_product
from .config import HEADERS


def scrape_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return parse_product(soup)
    except Exception as e:
        print(f"Hubo un error durante el scraping de la url {url}: {e}")
        return {}
