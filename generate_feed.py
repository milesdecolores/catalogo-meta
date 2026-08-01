from __future__ import annotations
import csv, hashlib, json, re, time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.milesdecolores.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.products.xml"
OUTPUT = Path("docs/catalogo-meta.csv")
session = requests.Session()
session.headers.update({"User-Agent": "MilesDeColores-MetaFeed/1.0"})

def clean(value):
    return re.sub(r"\s+", " ", BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)).strip()

def get_urls():
    r = session.get(SITEMAP_URL, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [n.text.strip() for n in root.findall(".//sm:loc", ns) if n.text]
    return urls or [n.text.strip() for n in root.findall(".//loc") if n.text]

def json_ld(soup):
    out = []
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(tag.get_text(strip=True))
        except Exception:
            continue
        for obj in (data if isinstance(data, list) else [data]):
            if isinstance(obj, dict):
                out.extend(x for x in obj.get("@graph", []) if isinstance(x, dict))
                out.append(obj)
    return out

def meta(soup, selector):
    node = soup.select_one(selector)
    return node.get("content", "").strip() if node else ""

def price_value(raw):
    m = re.search(r"(\d+(?:[.,]\d{1,2})?)", (raw or "").replace("\xa0", ""))
    if not m:
        raise ValueError("Precio no encontrado")
    return f"{float(m.group(1).replace(',', '.')):.2f} EUR"

def product_row(url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    product = {}
    for obj in json_ld(soup):
        types = obj.get("@type")
        types = types if isinstance(types, list) else [types]
        if "Product" in types:
            product = obj
            break

    title_node = soup.select_one("h1")
    title = clean(product.get("name") or meta(soup, 'meta[property="og:title"]') or (title_node.get_text(" ", strip=True) if title_node else ""))
    description = clean(product.get("description") or meta(soup, 'meta[name="description"]') or meta(soup, 'meta[property="og:description"]')) or title

    offers = product.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    raw_price = str(offers.get("price") or "")
    price = price_value(raw_price or soup.get_text(" ", strip=True))

    canonical = meta(soup, 'meta[property="og:url"]')
    c = soup.select_one('link[rel="canonical"]')
    canonical = canonical or (c.get("href", "") if c else "") or url
    canonical = urljoin(BASE_URL, canonical)

    image = product.get("image")
    if isinstance(image, list):
        image = image[0] if image else ""
    if isinstance(image, dict):
        image = image.get("url") or image.get("contentUrl") or ""
    image = image or meta(soup, 'meta[property="og:image"]') or meta(soup, 'meta[name="twitter:image"]')
    image = urljoin(BASE_URL, image)

    availability_raw = str(offers.get("availability") or "").lower()
    availability = "out of stock" if "outofstock" in availability_raw else "in stock"

    if not title or not image:
        raise ValueError("Falta título o imagen")

    return {
        "id": "mdc-" + hashlib.sha1(canonical.encode()).hexdigest()[:20],
        "title": title[:200],
        "description": description[:9999],
        "availability": availability,
        "condition": "new",
        "price": price,
        "link": canonical,
        "image_link": image,
        "brand": "Miles de Colores",
        "quantity_to_sell_on_facebook": "999" if availability == "in stock" else "0",
    }

def main():
    urls = get_urls()
    rows, errors = [], []
    for i, url in enumerate(urls, 1):
        try:
            rows.append(product_row(url))
            print(f"[{i}/{len(urls)}] OK {url}")
        except Exception as exc:
            errors.append(f"{url}\t{type(exc).__name__}: {exc}")
            print(f"[{i}/{len(urls)}] ERROR {url}: {exc}")
        time.sleep(0.15)

    OUTPUT.parent.mkdir(exist_ok=True)
    fields = ["id","title","description","availability","condition","price","link","image_link","brand","quantity_to_sell_on_facebook"]
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    Path("docs/errores.txt").write_text("\n".join(errors), encoding="utf-8")
    print(f"Feed creado: {len(rows)} productos; errores: {len(errors)}")

if __name__ == "__main__":
    main()
