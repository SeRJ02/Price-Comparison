# searcher.py — Cross-platform search

import time
import re
import json
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from config import HEADERS, AMAZON_SELECTORS, TOP_N_RESULTS, REQUEST_DELAY


def search_amazon(query: str) -> list:
    """Search Amazon.in and return top results."""
    try:
        url = f"https://www.amazon.in/s?k={quote_plus(query)}"
        resp = requests.get(url, headers=HEADERS["amazon"], timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        results = []
        cards = soup.select(AMAZON_SELECTORS["search_result"])
        for card in cards[:TOP_N_RESULTS]:
            title_el = card.select_one(AMAZON_SELECTORS["search_title"])
            price_el = card.select_one(AMAZON_SELECTORS["search_price"])
            link_el = card.select_one(AMAZON_SELECTORS["search_link"])

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            price_text = price_el.get_text(strip=True) if price_el else "0"
            # Clean price — remove commas, take integer
            price = 0
            try:
                price = int(re.sub(r"[^\d]", "", price_text))
            except ValueError:
                pass

            prod_url = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                prod_url = href if href.startswith("http") else f"https://www.amazon.in{href}"

            results.append({"title": title, "price": price, "url": prod_url})

        return results
    except Exception:
        return []


def search_flipkart(query: str) -> list:
    """Search Flipkart and return top results."""
    try:
        url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
        resp = requests.get(url, headers=HEADERS["flipkart"], timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        results = []
        # Flipkart search result cards — try multiple known container selectors
        cards = soup.select("div._1AtVbE, div._1xHGtK, div.slAVV4")
        for card in cards[:TOP_N_RESULTS * 2]:  # Over-select, filter later
            title_el = card.select_one("a.IRpwTa, a.s1Q9rs, div._4rR01T, a._2rpwqI")
            price_el = card.select_one("div._30jeq3, div._25b18c")
            link_el = card.select_one("a.IRpwTa, a.s1Q9rs, a._2rpwqI, a._1fQZEK")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            price = 0
            if price_el:
                try:
                    price = int(re.sub(r"[^\d]", "", price_el.get_text(strip=True)))
                except ValueError:
                    pass

            prod_url = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                prod_url = href if href.startswith("http") else f"https://www.flipkart.com{href}"

            results.append({"title": title, "price": price, "url": prod_url})

            if len(results) >= TOP_N_RESULTS:
                break

        return results
    except Exception:
        return []


def search_myntra(query: str) -> list:
    """Search Myntra. Tries JSON in script tag first, falls back to HTML."""
    try:
        search_slug = quote_plus(query).replace("+", "-")
        url = f"https://www.myntra.com/{search_slug}"
        resp = requests.get(url, headers=HEADERS["myntra"], timeout=15)
        resp.raise_for_status()

        results = []

        # Try extracting JSON from script tag (window.__myx or __INITIAL_STATE__)
        json_match = re.search(
            r'(?:window\.__myx\s*=|window\.__INITIAL_STATE__\s*=)\s*({.+?});?\s*</script>',
            resp.text, re.DOTALL
        )
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                # Navigate to product list — structure varies
                products = []
                if "searchData" in data:
                    products = data["searchData"].get("results", {}).get("products", [])
                elif "results" in data:
                    products = data["results"].get("products", [])

                for p in products[:TOP_N_RESULTS]:
                    title = f"{p.get('brand', '')} {p.get('productName', '')}".strip()
                    price = p.get("price", 0) or p.get("discountedPrice", 0)
                    prod_url = f"https://www.myntra.com/{p.get('landingPageUrl', '')}"
                    results.append({"title": title, "price": int(price), "url": prod_url})

                if results:
                    return results
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: parse HTML
        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".product-base, .results-base li")
        for card in cards[:TOP_N_RESULTS]:
            brand_el = card.select_one(".product-brand")
            name_el = card.select_one(".product-product")
            price_el = card.select_one(".product-discountedPrice, .product-price")
            link_el = card.select_one("a")

            brand = brand_el.get_text(strip=True) if brand_el else ""
            name = name_el.get_text(strip=True) if name_el else ""
            title = f"{brand} {name}".strip()
            if not title:
                continue

            price = 0
            if price_el:
                try:
                    price = int(re.sub(r"[^\d]", "", price_el.get_text(strip=True)))
                except ValueError:
                    pass

            prod_url = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                prod_url = href if href.startswith("http") else f"https://www.myntra.com{href}"

            results.append({"title": title, "price": price, "url": prod_url})

        return results
    except Exception:
        return []


def search_hamaramall(query: str) -> list:
    """Search Hamara Mall. URL pattern and selectors need live verification."""
    try:
        url = f"https://www.hamaramall.com/search?q={quote_plus(query)}"
        resp = requests.get(url, headers=HEADERS["hamaramall"], timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        results = []
        # Try common e-commerce search result patterns
        cards = soup.select(".product-card, .product-item, .search-result-item, .product-grid-item")
        for card in cards[:TOP_N_RESULTS]:
            title_el = card.select_one("h2, h3, .product-title, .product-name, a.product-link")
            price_el = card.select_one(".price, .product-price, .current-price")
            link_el = card.select_one("a")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            price = 0
            if price_el:
                try:
                    price = int(re.sub(r"[^\d]", "", price_el.get_text(strip=True)))
                except ValueError:
                    pass

            prod_url = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                prod_url = href if href.startswith("http") else f"https://www.hamaramall.com{href}"

            results.append({"title": title, "price": price, "url": prod_url})

        return results
    except Exception:
        return []


def search_all_platforms(product: dict, skip_platform: str) -> dict:
    """Search all platforms except the source. Returns dict of platform -> results list."""
    search_funcs = {
        "amazon": search_amazon,
        "flipkart": search_flipkart,
        "myntra": search_myntra,
        "hamaramall": search_hamaramall,
    }

    query = product.get("search_query", "")
    results = {}

    for platform, func in search_funcs.items():
        if platform == skip_platform:
            continue
        results[platform] = func(query)
        time.sleep(REQUEST_DELAY)

    return results
