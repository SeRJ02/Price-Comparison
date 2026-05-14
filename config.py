# config.py — All constants, headers, CSS selectors

# Platform domain detection
PLATFORM_DOMAINS = {
    "amazon.in": "amazon",
    "flipkart.com": "flipkart",
    "myntra.com": "myntra",
    "hamaramall.com": "hamaramall",
}

# Request headers per platform
HEADERS = {
    "amazon": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9",
    },
    "flipkart": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
    "myntra": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
    "hamaramall": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
}

# Matching score thresholds
SCORE_EXACT = 65      # Show as ✅ Exact match
SCORE_SIMILAR = 45    # Show as ⚠️ Similar product
# Below 40 = ❌ Not found

# Search result count to evaluate per platform
TOP_N_RESULTS = 5

# Delays between requests (seconds) to avoid rate limiting
REQUEST_DELAY = 1.5

# Google Sheet config
SHEET_NAME = "EarnKaro Commissions"
SHEET_TAB = "Category Commission"
COMMISSION_COL_CATEGORY = 0  # Column A
COMMISSION_COL_PERCENT = 1   # Column B

# CSS Selectors — Amazon
AMAZON_SELECTORS = {
    "brand": "#bylineInfo span",
    "title": "#productTitle",
    "price_primary": "#priceblock_ourprice",
    "price_whole": ".a-price-whole",
    "price_deal": "#priceblock_dealprice",
    "breadcrumb": "#wayfinding-breadcrumbs_feature_div",
    "search_result": 'div[data-component-type="s-search-result"]',
    "search_title": ".a-size-medium, .a-size-base-plus",
    "search_price": ".a-price-whole",
    "search_link": "a.a-link-normal",
}

# CSS Selectors — Flipkart
FLIPKART_SELECTORS = {
    "title": "._35KyD6, .B_NuCI",
    "price": "._30jeq3._16Jk6d",
    "breadcrumb": "._2whKao",
}

# CSS Selectors — Myntra
MYNTRA_SELECTORS = {
    "brand": ".pdp-title",
    "title": ".pdp-name",
    "price": ".pdp-price strong, .pdp-mrp",
}

# CSS Selectors — Hamara Mall (to be updated after live inspection)
HAMARAMALL_SELECTORS = {
    "brand": "",
    "title": "",
    "price": "",
    "category": "",
}

# Platform emoji map
PLATFORM_EMOJI = {
    "amazon": "🟠",
    "flipkart": "🟡",
    "myntra": "🔵",
    "hamaramall": "🏪",
}

# Stop words for keyword extraction
STOP_WORDS = {"for", "with", "and", "of", "the", "in", "a", "an", "-"}
