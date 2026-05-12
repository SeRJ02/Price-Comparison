# utils.py — Shared helpers

import re
from urllib.parse import urlparse
from config import PLATFORM_DOMAINS, STOP_WORDS


def detect_platform(url: str) -> str:
    """Parse URL domain and return platform name. Raises ValueError if unknown."""
    domain = urlparse(url).netloc.lower().replace("www.", "")
    for key, platform in PLATFORM_DOMAINS.items():
        if key in domain:
            return platform
    raise ValueError(f"Unrecognised domain: {domain}")


def normalize_quantity(text: str) -> str:
    """Standardize quantity strings for comparison."""
    if not text:
        return ""
    text = text.lower().strip().replace(" ", "")

    # Convert kg to g
    kg_match = re.match(r"^(\d+(?:\.\d+)?)kg$", text)
    if kg_match:
        grams = int(float(kg_match.group(1)) * 1000)
        return f"{grams}g"

    # Normalize "gm" to "g"
    text = re.sub(r"(\d)gm$", r"\1g", text)

    # Normalize "pack of N" / "xN" to "Npack"
    pack_match = re.match(r"packof(\d+)", text)
    if pack_match:
        return f"{pack_match.group(1)}pack"
    x_match = re.match(r"x(\d+)$", text)
    if x_match:
        return f"{x_match.group(1)}pack"

    return text


def extract_quantity_from_title(title: str) -> str:
    """Use regex to find quantity patterns in a product title."""
    if not title:
        return ""
    patterns = [
        r"(\d+(?:\.\d+)?\s*(?:ml|l|kg|g|gm|oz))\b",  # 250ml, 1.5kg, 200g, 100gm
        r"(pack\s*of\s*\d+)",                           # pack of 2
        r"\b(x\d+)\b",                                  # x3
    ]
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def clean_price(price_str: str) -> int:
    """Strip currency symbols, commas, decimals. Return integer price or 0."""
    if not price_str:
        return 0
    # Find the first number (with optional decimals)
    match = re.search(r"(\d[\d,]*(?:\.\d+)?)", price_str)
    if not match:
        return 0
    cleaned = match.group(1).replace(",", "")
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


def extract_keywords(title: str, brand: str) -> list:
    """Extract meaningful keywords from title, removing brand, stop words, quantity."""
    if not title:
        return []
    # Remove brand from title
    cleaned = re.sub(re.escape(brand), "", title, flags=re.IGNORECASE).strip()
    # Remove quantity strings
    qty = extract_quantity_from_title(cleaned)
    if qty:
        cleaned = cleaned.replace(qty, "")
    # Tokenize, lowercase, filter
    words = cleaned.lower().split()
    keywords = [w.strip(",-()") for w in words if w.strip(",-()") and w.strip(",-()") not in STOP_WORDS]
    return keywords
