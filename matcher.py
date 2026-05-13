# matcher.py — Hybrid scoring: rapidfuzz + hand-rolled TF-IDF + brand/qty/price signals

import math
import re
import time
from collections import Counter
from rapidfuzz import fuzz

from config import SCORE_EXACT, SCORE_SIMILAR, REQUEST_DELAY
from utils import normalize_quantity, extract_quantity_from_title


_WORD = re.compile(r"[a-z0-9]+")


def _tokenize(text):
    return _WORD.findall((text or "").lower())


def _tfidf_cosines(source_text, candidate_texts):
    """Return cosine(source, candidate) for each candidate using TF-IDF over the small corpus."""
    docs = [source_text] + list(candidate_texts)
    tokenized = [_tokenize(d) for d in docs]
    n = len(tokenized)
    df = Counter()
    for tokens in tokenized:
        for t in set(tokens):
            df[t] += 1
    idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}

    def vec(tokens):
        tf = Counter(tokens)
        return {t: f * idf[t] for t, f in tf.items()}

    vectors = [vec(t) for t in tokenized]

    def cosine(a, b):
        keys = set(a) | set(b)
        dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    src = vectors[0]
    return [cosine(src, v) for v in vectors[1:]]


def _quantity_match(source_qty, result_title):
    if not source_qty:
        return False
    res_qty = extract_quantity_from_title(result_title)
    if not res_qty:
        return False
    return normalize_quantity(source_qty) == normalize_quantity(res_qty)


def _price_sanity(source_price, result_price):
    if not source_price or not result_price:
        return 0
    ratio = result_price / source_price
    if 0.2 <= ratio <= 5.0:
        return 5
    return -5


def score_result(source, result):
    """Score 0-100. Result must have '_tfidf' key (cosine 0-1) injected by pick_best_match."""
    src_name = source.get("name") or source.get("search_query") or ""
    res_title = result.get("title", "")
    if not res_title:
        return 0

    fuzzy = fuzz.token_set_ratio(src_name, res_title) / 100.0 * 40
    tfidf = result.get("_tfidf", 0) * 30
    brand = (source.get("brand") or "").lower()
    brand_score = 15 if brand and brand in res_title.lower() else 0
    qty_score = 10 if _quantity_match(source.get("quantity"), res_title) else 0
    price_score = _price_sanity(source.get("price"), result.get("price"))

    total = fuzzy + tfidf + brand_score + qty_score + price_score
    return int(max(0, min(100, total)))


def pick_best_match(source, results):
    if not results:
        return {"match_type": "not_found", "score": 0}

    src_text = source.get("name") or source.get("search_query") or ""
    titles = [r.get("title", "") for r in results]
    cosines = _tfidf_cosines(src_text, titles)

    best = None
    best_score = -1
    for r, cos in zip(results, cosines):
        enriched = dict(r)
        enriched["_tfidf"] = cos
        s = score_result(source, enriched)
        print(f"[match] score={s} tfidf={cos:.2f} title={r.get('title','')!r}")
        if s > best_score:
            best_score = s
            best = enriched

    if best is None:
        return {"match_type": "not_found", "score": 0}

    match = {k: v for k, v in best.items() if not k.startswith("_")}
    match["score"] = best_score
    if best_score >= SCORE_EXACT:
        match["match_type"] = "exact"
    elif best_score >= SCORE_SIMILAR:
        match["match_type"] = "similar"
    else:
        match["match_type"] = "not_found"
    return match


def fallback_search(source, platform):
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

    query1 = f"{brand} {' '.join(keywords[:5])}".strip()
    if query1:
        time.sleep(REQUEST_DELAY)
        results = func(query1)
        match = pick_best_match(source, results)
        if match["match_type"] != "not_found":
            return match

    query2 = " ".join(keywords[:3]).strip()
    if query2:
        time.sleep(REQUEST_DELAY)
        results = func(query2)
        match = pick_best_match(source, results)
        if match["match_type"] != "not_found":
            return match

    return {"match_type": "unavailable"}


def match_all_platforms(source, search_results):
    matches = {}
    for platform, results in search_results.items():
        match = pick_best_match(source, results)
        if match["match_type"] == "not_found":
            match = fallback_search(source, platform)
        matches[platform] = match
    return matches
