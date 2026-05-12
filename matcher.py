# matcher.py — Scoring & match selection

import time
from config import SCORE_EXACT, SCORE_SIMILAR, REQUEST_DELAY
from utils import normalize_quantity, extract_quantity_from_title


def score_result(source: dict, result: dict) -> int:
    """Score a single search result against the source product (max 100)."""
    score = 0

    # Rule 1 — Brand match (required gate, +40)
    if source.get("brand") and source["brand"].lower() not in result.get("title", "").lower():
        return 0
    score += 40

    # Rule 2 — Quantity match (+35)
    source_qty = normalize_quantity(source.get("quantity", ""))
    result_qty = extract_quantity_from_title(result.get("title", ""))
    if source_qty and result_qty and source_qty == normalize_quantity(result_qty):
        score += 35

    # Rule 3 — Keyword overlap (+25)
    source_kw = set(source.get("keywords", []))
    result_words = set(result.get("title", "").lower().split())
    if source_kw:
        overlap = len(source_kw & result_words) / len(source_kw)
        score += int(overlap * 25)

    return score


def pick_best_match(source: dict, results: list) -> dict:
    """Score all results, return best with score and match_type."""
    if not results:
        return {"match_type": "not_found", "score": 0}

    best = None
    best_score = -1

    for r in results:
        s = score_result(source, r)
        if s > best_score:
            best_score = s
            best = r

    if best is None:
        return {"match_type": "not_found", "score": 0}

    match = dict(best)
    match["score"] = best_score
    if best_score >= SCORE_EXACT:
        match["match_type"] = "exact"
    elif best_score >= SCORE_SIMILAR:
        match["match_type"] = "similar"
    else:
        match["match_type"] = "not_found"

    return match


def fallback_search(source: dict, platform: str) -> dict:
    """Re-search with relaxed queries when best score is not_found."""
    from searcher import search_amazon, search_flipkart, search_myntra, search_hamaramall

    search_funcs = {
        "amazon": search_amazon,
        "flipkart": search_flipkart,
        "myntra": search_myntra,
        "hamaramall": search_hamaramall,
    }
    func = search_funcs.get(platform)
    if not func:
        return {"match_type": "unavailable"}

    brand = source.get("brand", "")
    keywords = source.get("keywords", [])

    # Fallback 1: brand + product name (no quantity)
    query1 = f"{brand} {' '.join(keywords[:5])}".strip()
    if query1:
        time.sleep(REQUEST_DELAY)
        results = func(query1)
        match = pick_best_match(source, results)
        if match["match_type"] != "not_found":
            return match

    # Fallback 2: product type + key ingredient (no brand)
    query2 = " ".join(keywords[:3]).strip()
    if query2:
        time.sleep(REQUEST_DELAY)
        results = func(query2)
        match = pick_best_match(source, results)
        if match["match_type"] != "not_found":
            return match

    return {"match_type": "unavailable"}


def match_all_platforms(source: dict, search_results: dict) -> dict:
    """For each platform, pick best match; fallback if not_found."""
    matches = {}
    for platform, results in search_results.items():
        match = pick_best_match(source, results)
        if match["match_type"] == "not_found":
            match = fallback_search(source, platform)
        matches[platform] = match
    return matches
