# === COLAB CELL: Unit Tests — utils.py (Task 9.1) ===

from utils import detect_platform, normalize_quantity, extract_quantity_from_title, clean_price, extract_keywords

# detect_platform
assert detect_platform("https://www.amazon.in/dp/B08XYZ") == "amazon"
assert detect_platform("https://www.flipkart.com/some-product") == "flipkart"
assert detect_platform("https://www.myntra.com/shirts/123") == "myntra"
assert detect_platform("https://www.hamaramall.com/product/456") == "hamaramall"
try:
    detect_platform("https://www.unknown.com/abc")
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("✅ detect_platform passed")

# normalize_quantity
assert normalize_quantity("250 ML") == "250ml"
assert normalize_quantity("1 KG") == "1000g"
assert normalize_quantity("250ml") == "250ml"
assert normalize_quantity("100gm") == "100g"
assert normalize_quantity("pack of 3") == "3pack"
assert normalize_quantity("x3") == "3pack"
assert normalize_quantity("") == ""
print("✅ normalize_quantity passed")

# extract_quantity_from_title
assert extract_quantity_from_title("Mamaearth Onion Hair Oil 250ml") == "250ml"
assert extract_quantity_from_title("Protein Powder 1kg Pack") == "1kg"
assert extract_quantity_from_title("Face Wash 200g") == "200g"
assert extract_quantity_from_title("Soap pack of 3") == "pack of 3"
assert extract_quantity_from_title("Shampoo 500 ml bottle") == "500 ml"
assert extract_quantity_from_title("No quantity here") == ""
print("✅ extract_quantity_from_title passed")

# clean_price
assert clean_price("\u20b91,299") == 1299
assert clean_price("Rs. 1299.00") == 1299
assert clean_price("\u20b9599") == 599
assert clean_price("") == 0
assert clean_price("abc") == 0
print("✅ clean_price passed")

# extract_keywords
kw = extract_keywords("Mamaearth Onion Hair Oil for Hair Growth & Hair Fall Control 250ml", "Mamaearth")
assert "onion" in kw
assert "hair" in kw
assert "oil" in kw
assert "mamaearth" not in kw
assert "for" not in kw
print("✅ extract_keywords passed")

print("\n🎉 All utils.py tests passed!")
