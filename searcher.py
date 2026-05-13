# searcher.py — Cross-platform search

import os
import time
import re
import json
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from config import HEADERS, TOP_N_RESULTS, REQUEST_DELAY


SCRAPER_PARAMS = {
    "flipkart": "&country_code=in&render=true",
}


def fetch(url, platform):
    scraper_key = os.environ.get("SCRAPER_API_KEY", "")
    if scraper_key:
        extra = SCRAPER_PARAMS.get(platform, "")
        fetch_url = f"http://api.scraperapi.com?api_key={scraper_key}&url={url}{extra}"
    else:
        fetch_url = url
    headers = HEADERS.get(platform, {})
    resp = requests.get(fetch_url, headers=headers, timeout=90)
    resp.raise_for_status()
    return resp.text


def clean_int(text):
    try:
        return int(re.sub(r"[^\d]", "", text or ""))
    except (ValueError, TypeError):
        return 0


def search_amazon(query):
    try:
        html = fetch(f"https://www.amazon.in/s?k={quote_plus(query)}", "amazon")
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for card in soup.select("div[data-component-type='s-search-result'], div.s-result-item")[:TOP_N_RESULTS * 2]:
            title_el = card.select_one("h2 span, .a-size-medium, .a-size-base-plus")
            price_el = card.select_one(".a-price-whole, .a-offscreen")
            link_el = card.select_one("h2 a, a.a-link-normal")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            price = clean_int(price_el.get_text(strip=True) if price_el else "")
            href = link_el.get("href", "") if link_el else ""
            prod_url = href if href.startswith("http") else f"https://www.amazon.in{href}"
            results.append({"title": title, "price": price, "url": prod_url})
            if len(results) >= TOP_N_RESULTS:
                break
        return results
    except Exception as e:
        print(f"[search_amazon] error: {e}")
        return []


def search_flipkart(query):
    html = ""
    try:
        html = fetch(f"https://www.flipkart.com/search?q={quote_plus(query)}", "flipkart")
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for card in soup.select("div[data-id]"):
            title_el = card.select_one("a[title]")
            if not title_el:
                continue
            title = title_el.get("title", "").strip()
            if len(title) < 5:
                continue
            href = title_el.get("href", "")
            prod_url = href if href.startswith("http") else f"https://www.flipkart.com{href}"
            price = 0
            for el in card.find_all(string=True):
                txt = el.strip()
                if txt.startswith("\u20b9"):
                    price = clean_int(txt)
                    break
            results.append({"title": title, "price": price, "url": prod_url})
            if len(results) >= TOP_N_RESULTS:
                break
        if not results:
            print(f"[flipkart-debug] html_len={len(html)} head={html[:1500]!r}")
        return results
    except Exception as e:
        print(f"[search_flipkart] error: {e}")
        return []


def search_myntra(query):
    try:
        slug = quote_plus(query).replace("+", "-")
        html = fetch(f"https://www.myntra.com/{slug}", "myntra")
        results = []
        m = re.search(r'(?:window\.__myx\s*=|window\.__INITIAL_STATE__\s*=)\s*({.+?});?\s*</script>', html, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                products = []
                if "searchData" in data:
                    products = data["searchData"].get("results", {}).get("products", [])
                elif "results" in data:
                    products = data["results"].get("products", [])
                for p in products[:TOP_N_RESULTS]:
                    title = f"{p.get('brand', '')} {p.get('productName', '')}".strip()
                    price = int(p.get("price", 0) or p.get("discountedPrice", 0) or 0)
                    prod_url = f"https://www.myntra.com/{p.get('landingPageUrl', '')}"
                    results.append({"title": title, "price": price, "url": prod_url})
                if results:
                    return results
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".product-base, .results-base li, li.product-base")[:TOP_N_RESULTS]:
            brand_el = card.select_one(".product-brand")
            name_el = card.select_one(".product-product")
            price_el = card.select_one(".product-discountedPrice, .product-price")
            link_el = card.select_one("a")
            brand = brand_el.get_text(strip=True) if brand_el else ""
            name = name_el.get_text(strip=True) if name_el else ""
            title = f"{brand} {name}".strip()
            if not title:
                continue
            price = clean_int(price_el.get_text(strip=True) if price_el else "")
            href = link_el.get("href", "") if link_el else ""
            prod_url = href if href.startswith("http") else f"https://www.myntra.com{href}"
            results.append({"title": title, "price": price, "url": prod_url})
        return results
    except Exception as e:
        print(f"[search_myntra] error: {e}")
        return []


def search_hamaramall(query):
    try:
        html = fetch(f"https://www.hamaramall.com/search?q={quote_plus(query)}", "hamaramall")
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for card in soup.select(".product-card, .product-item, .search-result-item, .product-grid-item")[:TOP_N_RESULTS]:
            title_el = card.select_one("h2, h3, .product-title, .product-name, a.product-link")
            price_el = card.select_one(".price, .product-price, .current-price")
            link_el = card.select_one("a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            price = clean_int(price_el.get_text(strip=True) if price_el else "")
            href = link_el.get("href", "") if link_el else ""
            prod_url = href if href.startswith("http") else f"https://www.hamaramall.com{href}"
            results.append({"title": title, "price": price, "url": prod_url})
        return results
    except Exception as e:
        print(f"[search_hamaramall] error: {e}")
        return []


def search_all_platforms(product, skip_platform):
    search_funcs = {"amazon": search_amazon, "flipkart": search_flipkart, "myntra": search_myntra, "hamaramall": search_hamaramall}
    query = product.get("search_query", "")
    results = {}
    for platform, func in search_funcs.items():
        if platform == skip_platform:
            continue
        results[platform] = func(query)
        print(f"[search] {platform}: found {len(results[platform])} results")
        for i, r in enumerate(results[platform][:5]):
            print(f"[search]   {platform}[{i}] title={r.get('title','')!r} price={r.get('price',0)}")
        time.sleep(REQUEST_DELAY)
    return results
