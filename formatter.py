# formatter.py — Telegram message builder

from config import PLATFORM_EMOJI, SCORE_EXACT


def format_platform_row(platform: str, match: dict, source_platform: str) -> str:
    """Build one line of the price comparison table."""
    emoji = PLATFORM_EMOJI.get(platform, "❓")
    name = platform.capitalize()
    if platform == "hamaramall":
        name = "Hamara Mall"

    suffix = " (your link)" if platform == source_platform else ""

    match_type = match.get("match_type", "unavailable")
    if match_type == "unavailable":
        return f"{emoji} {name:<12} —    ❌ not listed"
    if match_type == "not_found":
        return f"{emoji} {name:<12} —    ❌ not found"

    price = match.get("price", 0)
    price_str = f"₹{price}" if price else "—"

    if match_type == "exact":
        indicator = "✅"
    elif match_type == "similar":
        indicator = "⚠️ similar"
    else:
        indicator = "❌"

    return f"{emoji} {name:<12} {price_str:<8} {indicator}{suffix}"


def find_best_deal(matches: dict) -> tuple:
    """Find cheapest platform and best earning platform among exact matches.
    Returns (cheapest_platform, best_earning_platform)."""
    cheapest_platform = None
    cheapest_price = float("inf")
    best_earning_platform = None
    best_earning = 0.0

    for platform, match in matches.items():
        if match.get("match_type") != "exact":
            continue
        price = match.get("price", 0)
        if price and price < cheapest_price:
            cheapest_price = price
            cheapest_platform = platform

    return cheapest_platform, cheapest_price


def format_full_message(source: dict, matches: dict, commission: float) -> str:
    """Assemble the complete Telegram message."""
    brand = source.get("brand", "")
    name = source.get("name", "")
    quantity = source.get("quantity", "")
    category = source.get("category", "")
    source_platform = source.get("platform", "")

    # Header
    lines = [
        f"🔍 {brand} {name} {quantity}".strip(),
        f"📂 {category} | 💸 EarnKaro Commission: {commission}%" if commission else f"📂 {category}",
        "",
        "💰 Price Comparison",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    # Source platform row first
    if source_platform:
        source_match = {
            "match_type": "exact",
            "price": source.get("price", 0),
        }
        lines.append(format_platform_row(source_platform, source_match, source_platform))

    # Other platforms
    platform_order = ["amazon", "flipkart", "myntra", "hamaramall"]
    for p in platform_order:
        if p == source_platform:
            continue
        if p in matches:
            lines.append(format_platform_row(p, matches[p], source_platform))

    # Best deal
    cheapest_platform, cheapest_price = find_best_deal(matches)
    # Also check source price
    source_price = source.get("price", 0)
    if source_price and (not cheapest_platform or source_price < cheapest_price):
        cheapest_platform = source_platform
        cheapest_price = source_price

    if cheapest_platform:
        lines.append("")
        p_name = "Hamara Mall" if cheapest_platform == "hamaramall" else cheapest_platform.capitalize()
        lines.append(f"🏆 Lowest price: {p_name} ₹{cheapest_price}")

    # Best earning
    if commission and cheapest_platform:
        earning = round(cheapest_price * commission / 100, 2)
        lines.append(f"💡 Best earning: {p_name} → ₹{earning}")

    # Similar warning
    has_similar = any(m.get("match_type") == "similar" for m in matches.values())
    if has_similar:
        lines.append("")
        lines.append("⚠️ Note: Similar products may differ in size/variant")

    return "\n".join(lines)
