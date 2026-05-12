# === COLAB CELL: Unit Tests — matcher.py (Task 9.3) ===

from matcher import score_result, pick_best_match

source = {
    "brand": "Mamaearth",
    "quantity": "250ml",
    "keywords": ["onion", "hair", "oil", "growth", "control"],
}

result_exact = {"title": "Mamaearth Onion Hair Oil 250ml", "price": 299}
result_similar = {"title": "Mamaearth Onion Hair Oil 100ml", "price": 199}
result_different = {"title": "WOW Onion Hair Oil 250ml", "price": 280}

# score_result
s_exact = score_result(source, result_exact)
s_similar = score_result(source, result_similar)
s_different = score_result(source, result_different)
print(f"Scores — exact: {s_exact}, similar: {s_similar}, different brand: {s_different}")

assert s_exact >= 75, f"Expected >=75, got {s_exact}"
assert 40 <= s_similar < 75, f"Expected 40-74, got {s_similar}"
assert s_different == 0, f"Expected 0 (brand mismatch), got {s_different}"
print("✅ score_result passed")

# pick_best_match — should pick exact
best = pick_best_match(source, [result_exact, result_similar, result_different])
assert best["match_type"] == "exact"
assert best["score"] >= 75
print(f"✅ pick_best_match picked: score={best['score']}, type={best['match_type']}")

# pick_best_match — empty list
empty = pick_best_match(source, [])
assert empty["match_type"] == "not_found"
print("✅ pick_best_match empty list → not_found")

# pick_best_match — only similar
best_sim = pick_best_match(source, [result_similar])
assert best_sim["match_type"] == "similar"
print(f"✅ pick_best_match similar only: score={best_sim['score']}, type={best_sim['match_type']}")

# pick_best_match — only brand mismatch
best_diff = pick_best_match(source, [result_different])
assert best_diff["match_type"] == "not_found"
print("✅ pick_best_match brand mismatch → not_found")

print("\n🎉 All matcher.py tests passed!")
