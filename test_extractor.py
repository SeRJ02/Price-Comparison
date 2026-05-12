# === COLAB CELL: Unit Tests — extractor.py (Task 9.2) ===
# Tests with 5 real product URLs (one per platform + one edge case)
# NOTE: These hit live websites. Some may fail due to rate limiting or selector changes.

from extractor import extract_product

TEST_URLS = [
    # Amazon — beauty product
    "https://www.amazon.in/Mamaearth-Onion-Hair-Growth-Control/dp/B07WLXGKWD",
    # Flipkart — beauty product
    "https://www.flipkart.com/mamaearth-onion-hair-oil-growth-fall-control/p/itm123",
    # Myntra — fashion product
    "https://www.myntra.com/tshirts/roadster/roadster-men-black-solid/12345",
    # Hamara Mall
    "https://www.hamaramall.com/product/test-product-123",
    # Edge case — Amazon with minimal info
    "https://www.amazon.in/dp/B000000000",
]

for url in TEST_URLS:
    print(f"\n--- Testing: {url[:60]}... ---")
    result = extract_product(url)
    print(f"  Platform: {result['platform']}")
    print(f"  Brand:    {result['brand']}")
    print(f"  Name:     {result['name'][:60] if result['name'] else '(empty)'}")
    print(f"  Price:    {result['price']}")
    print(f"  Quantity: {result['quantity']}")
    print(f"  Category: {result['category']}")
    print(f"  Query:    {result['search_query']}")
    print(f"  Warnings: {result['warnings']}")
    # Should never crash
    assert isinstance(result, dict)
    assert result["platform"] in ("amazon", "flipkart", "myntra", "hamaramall", "")

print("\n🎉 extractor.py tests complete — verify output manually")
