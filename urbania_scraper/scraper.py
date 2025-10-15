import time
import xml.etree.ElementTree as ET
import requests

from urbania_scraper.config import HEADERS, SITEMAPS, REQUEST_DELAY_SITEMAP, REQUEST_DELAY_PAGE, MAX_URLS
from urbania_scraper.parser import parse_property_html

def _get(url, timeout=30):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r

def fetch_inmueble_urls_from_sitemaps(max_urls=None):
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    seen, urls = set(), []

    def walk(sm_url):
        time.sleep(REQUEST_DELAY_SITEMAP)
        try:
            root = ET.fromstring(_get(sm_url).content)
        except Exception:
            return
        # Índice
        for sm in root.findall("sm:sitemap", ns):
            loc = sm.findtext("sm:loc", namespaces=ns)
            if loc and loc not in seen:
                seen.add(loc); walk(loc)
        # URLs
        for u in root.findall("sm:url", ns):
            loc = u.findtext("sm:loc", namespaces=ns) or ""
            if "/inmueble/" in loc:
                urls.append(loc)

    for sm in SITEMAPS:
        walk(sm)

    urls = list(dict.fromkeys(urls))
    return urls[:max_urls] if max_urls else urls

def scrape_urbania_san_miguel(urls):
    rows = []
    ok = skipped = errors = 0

    for url in urls:
        try:
            time.sleep(REQUEST_DELAY_PAGE)
            html = _get(url).text
            rec = parse_property_html(url, html)
            if rec:
                rows.append(rec)
                ok += 1
            else:
                skipped += 1
        except KeyboardInterrupt:
            break
        except Exception as e:
            errors += 1
    return rows, ok, skipped, errors
