from bs4 import BeautifulSoup

def parse_product(soup: BeautifulSoup):
    product = {}

    # Establecer los selectores del DOM y el CSS
    # se usa # porque productTitle es el id
    title_tag = soup.select_one("span#productTitle")
    # se usa . por que a-price-whole es la clase CSS
    price_tag = soup.select_one("span.a-price-whole")

    product["title"] = title_tag.get_text(strip=True) if title_tag else None
    product["price"] = price_tag.get_text(strip=True) if price_tag else None

    return product
