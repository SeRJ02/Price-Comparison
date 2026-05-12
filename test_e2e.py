# === COLAB CELL: End-to-End Test (Task 9.4) ===
# Runs the full pipeline with mock search results to verify integration.
# For live testing, replace mock patches with real URLs.

import unittest.mock as mock
from extractor import extract_product, build_search_query
from searcher import search_all_platforms
from matcher import match_all_platforms
from sheets import get_commission
from formatter import format_full_message

# Mock commission map
commission_map = {
    "Hair Care": 12.0,
    "Skin Care": 10.0,
    "Electronics": 5.0,
}

# --- Test Case 1: Full pipeline with mock data ---
print("=" * 50)
print("TEST 1: Full pipeline (mock data)")
print("=" * 50)

# Simulate extracted product
product = {
    "platform": "amazon",
    "url": "https://www.amazon.in/Mamaearth-Onion-Hair-Oil/dp/B07WLXGKWD",
    "brand": "Mamaearth",
    "name": "Onion Hair Oil for Hair Growth & Hair Fall Control",
    "quantity": "250ml",
    "keywords": ["onion", "hair", "oil", "growth", "control"],
    "category": "Hair Care",
    "price": 299,
    "search_query": "Mamaearth onion hair oil growth control 250ml",
    "warnings": [],
}

# Mock search results
mock_search_results = {
    "flipkart": [
        {"title": "Mamaearth Onion Hair Oil 250ml", "price": 319, "url": "https://flipkart.com/..."},
        {"title": "Mamaearth Onion Shampoo 250ml", "price": 349, "url": "https://flipkart.com/..."},
    ],
    "myntra": [
        {"title": "Mamaearth Onion Hair Oil 100ml", "price": 199, "url": "https://myntra.com/..."},
    ],
    "hamaramall": [],
}

# Run matching
matches = match_all_platforms(product, mock_search_results)
commission = get_commission(product["category"], commission_map)
message = format_full_message(product, matches, commission)

print(message)
print()
assert "Mamaearth" in message
assert "12.0%" in message
assert "✅" in message
print("✅ Test 1 passed\n")

# --- Test Case 2: No matches found ---
print("=" * 50)
print("TEST 2: No matches on any platform")
print("=" * 50)

mock_empty = {
    "flipkart": [],
    "myntra": [],
    "hamaramall": [],
}

with mock.patch("matcher.fallback_search", return_value={"match_type": "unavailable"}):
    matches2 = match_all_platforms(product, mock_empty)
message2 = format_full_message(product, matches2, commission)

print(message2)
print()
assert "not listed" in message2 or "not found" in message2 or "unavailable" in message2.lower()
print("✅ Test 2 passed\n")

# --- Test Case 3: Product with no commission ---
print("=" * 50)
print("TEST 3: Unknown category (0% commission)")
print("=" * 50)

product3 = dict(product)
product3["category"] = "Unknown Category"
commission3 = get_commission(product3["category"], commission_map)
message3 = format_full_message(product3, matches, commission3)

print(message3)
print()
assert commission3 == 0.0
print("✅ Test 3 passed\n")

print("🎉 All end-to-end tests passed!")
