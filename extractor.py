# extractor.py — Source page scraper

import os
import time
import requests
from bs4 import BeautifulSoup

from config import HEADERS, AMAZON_SELECTORS, FLIPKART_SELECTORS, MYNTRA_SELECTORS, HAMARAMALL_SELECTORS
from utils import detect_platform, extract_quantity_from_title, extract_keywords, clean_price

FULL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def extract_product(url: str) -> dict:
    """Main entry: fetch URL, detect platform, extract structured product data."""
    product = {
        "platform": "",
        "url": url,
        "brand": "",
        "name": "",
        "quantity": "",
        "keywords": [],
        "category": "",
        "price": 0,
        "search_query": "",
        "warnings": [],
    }

    try:
        platform = detect_platform(url)
        product["platform"] = platform

        session = requests.Session()
        headers = {**FULL_HEADERS, **HEADERS.get(platform, {})}
        session.headers.update(headers)
        scraper_key = os.environ.get("SCRAPER_API_KEY", "")
        if scraper_key:
            fetch_url = f"http://api.scraperapi.com?api_key={scraper_key}&url={url}"
        else:
            fetch_url = url
        resp = session.get(fetch_url, timeout=60)
        resp.raise_for_status()

        if len(resp.text) < 5000:
            raise Exception(f"Blocked or empty response from {platform} (got {len(resp.text)} bytes)")

        soup = BeautifulSoup(resp.text, "html.parser")

        extractors = {
            "amazon": extract_from_amazon,
            "flipkart": extract_from_flipkart,
            "myntra": extract_from_myntra,
            "hamaramall": extract_from_hamaramall,
        }

        extractor = extractors.get(platform)
        if extractor:
            data = extractor(soup, url)
            product.update(data)

        # Fill derived fields
        if product["name"] and not product["quantity"]:
            product["quantity"] = extract_quantity_from_title(product["name"])
        if product["name"] and product["brand"]:
            product["keywords"] = extract_keywords(product["name"], product["brand"])
        product["search_query"] = build_search_query(product)

    except Exception as e:
        product["warnings"].append(f"Extraction error: {str(e)}")

    return product


def extract_from_amazon(soup, url) -> dict:
    """Scrape an Amazon.in product page."""
    data = {"warnings": []}

    # Brand
    try:
        brand_el = soup.select_one(AMAZON_SELECTORS["brand"])
        if brand_el:
            data["brand"] = brand_el.get_text(strip=True)
        else:
            # Fallback: first word of title
            title_el = soup.select_one(AMAZON_SELECTORS["title"])
            if title_el:
                data["brand"] = title_el.get_text(strip=True).split()[0]
    except Exception:
        data["warnings"].append("brand selector failed")

    # Title
    try:
        title_el = soup.select_one(AMAZON_SELECTORS["title"])
        data["name"] = title_el.get_text(strip=True) if title_el else ""
    except Exception:
        data["warnings"].append("title selector failed")

    # Price — try multiple selectors in order
    try:
        price_text = ""
        for sel_key in ["price_primary", "price_whole", "price_deal"]:
            el = soup.select_one(AMAZON_SELECTORS[sel_key])
            if el:
                price_text = el.get_text(strip=True)
                break
        data["price"] = clean_price(price_text)
    except Exception:
        data["warnings"].append("price selector failed")

    # Category — breadcrumb second-to-last item
    try:
        breadcrumb = soup.select_one(AMAZON_SELECTORS["breadcrumb"])
        if breadcrumb:
            items = breadcrumb.select("a")
            if len(items) >= 2:
                data["category"] = items[-2].get_text(strip=True)
            elif items:
                data["category"] = items[-1].get_text(strip=True)
    except Exception:
        data["warnings"].append("category selector failed")

    # Quantity
    data["quantity"] = extract_quantity_from_title(data.get("name", ""))

    return data


def extract_from_flipkart(soup, url) -> dict:
    """Scrape a Flipkart product page."""
    data = {"warnings": []}

    # Title — prefer og:title (untruncated), fall back to h1
    name = ""
    og = soup.select_one('meta[property="og:title"]')
    if og and og.get("content"):
        name = og["content"].strip()
    if not name:
        h1 = soup.select_one("h1")
        if h1:
            name = h1.get_text(strip=True)
    # Strip trailing UI noise
    name = re.sub(r"\s*(\.{2,}\s*more|see\s+more|show\s+more)\s*$", "", name, flags=re.IGNORECASE).strip()
    data["name"] = name

    # Price — find any element with font="default-fk-font-m" containing ₹, else first ₹ in body
    price_text = ""
    for el in soup.select('[font="default-fk-font-m"]'):
        t = el.get_text(strip=True)
        if t.startswith("\u20b9"):
            price_text = t
            break
    if not price_text:
        for el in soup.find_all(string=True):
            t = el.strip()
            if t.startswith("\u20b9") and any(ch.isdigit() for ch in t):
                price_text = t
                break
    data["price"] = clean_price(price_text)

    # Brand — first word of URL slug (e.g. cetaphil-... -> Cetaphil)
    brand = ""
    try:
        path = url.split("flipkart.com/", 1)[-1]
        slug = path.split("/", 1)[0]
        first = slug.split("-")[0]
        if first.isalpha() and 2 <= len(first) <= 30:
            brand = first.capitalize()
    except Exception:
        pass
    if not brand and data.get("name"):
        brand = data["name"].split()[0]
    data["brand"] = brand

    # Category — from breadcrumb (links near top of page)
    try:
        crumbs = soup.select('a[href*="/store/"], nav a, ._3GIHBu a')
        texts = [a.get_text(strip=True) for a in crumbs if a.get_text(strip=True)]
        if len(texts) >= 2:
            data["category"] = texts[-2]
        elif texts:
            data["category"] = texts[-1]
    except Exception:
        data["warnings"].append("category selector failed")

    data["quantity"] = extract_quantity_from_title(data.get("name", ""))
    return data




def extract_from_myntra(soup, url) -> dict:
    """Scrape a Myntra product page."""
    data = {"warnings": []}

    # Brand
    try:
        brand_el = soup.select_one(MYNTRA_SELECTORS["brand"])
        data["brand"] = brand_el.get_text(strip=True) if brand_el else ""
    except Exception:
        data["warnings"].append("brand selector failed")

    # Title
    try:
        title_el = soup.select_one(MYNTRA_SELECTORS["title"])
        data["name"] = title_el.get_text(strip=True) if title_el else ""
    except Exception:
        data["warnings"].append("title selector failed")

    # Price
    try:
        price_el = soup.select_one(MYNTRA_SELECTORS["price"])
        data["price"] = clean_price(price_el.get_text(strip=True)) if price_el else 0
    except Exception:
        data["warnings"].append("price selector failed")

    # Category — parse from URL slug (Myntra URLs: /brand/product/category/)
    try:
        parts = [p for p in url.split("/") if p]
        if len(parts) >= 4:
            data["category"] = parts[3].replace("-", " ").title()
    except Exception:
        data["warnings"].append("category selector failed")

    # Quantity
    data["quantity"] = extract_quantity_from_title(data.get("name", ""))

    return data


def extract_from_hamaramall(soup, url) -> dict:
    """Scrape a Hamara Mall product page. Selectors TBD — needs live inspection."""
    data = {"warnings": []}

    # Attempt generic extraction using common patterns
    try:
        # Try common title selectors
        for sel in ["h1.product-title", "h1.product-name", "h1", ".product-title", ".product-name"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                data["name"] = el.get_text(strip=True)
                break
        if not data.get("name"):
            data["warnings"].append("title selector failed — needs live inspection")
    except Exception:
        data["warnings"].append("title selector failed")

    # Try common price selectors
    try:
        for sel in [".product-price", ".price", ".current-price", "span.price"]:
            el = soup.select_one(sel)
            if el:
                data["price"] = clean_price(el.get_text(strip=True))
                break
    except Exception:
        data["warnings"].append("price selector failed")

    # Brand — first word of title as fallback
    if data.get("name") and not data.get("brand"):
        data["brand"] = data["name"].split()[0]

    # Quantity
    data["quantity"] = extract_quantity_from_title(data.get("name", ""))

    return data


def build_search_query(product: dict) -> str:
    """Combine brand + core name + quantity into a search string (max 60 chars)."""
    parts = []
    if product.get("brand"):
        parts.append(product["brand"])
    if product.get("keywords"):
        parts.extend(product["keywords"][:5])  # Limit to top keywords
    if product.get("quantity"):
        parts.append(product["quantity"])
    query = " ".join(parts)
    return query[:60].strip()
