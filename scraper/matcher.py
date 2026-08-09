"""
Turns raw per-retailer search results into a clean, matched dataset.

Two jobs:
  1. pick_best_match() — a search page returns several products; this picks
     the one whose title most closely matches the part we're actually
     looking for.
  2. build_dashboard() — groups matched offers by part_key and works out the
     cheapest current price + the full comparison list.
"""

import difflib
import re

DISTINGUISHING_SUFFIXES = {"xt", "ti", "super", "gre", "plus"}

BRAND_ALIASES = {"nvidia": "geforce", "amd": "radeon"}

# Manufacturer/AIB brand words. When the target part_key names a specific
# brand (e.g. "MSI B850 Gaming Plus WiFi"), the candidate title MUST contain
# that same brand word — confirmed necessary after a real bug: a search for
# an MSI motherboard matched an Asus board instead, because both happened
# to share the chipset number (850) and no suffix conflict. Numeric +
# suffix gates alone don't catch a same-tier, wrong-manufacturer mismatch;
# only an explicit brand check does.
BRAND_KEYWORDS = {
    "msi", "asus", "gigabyte", "asrock", "sapphire", "powercolor", "xfx",
    "kingston", "corsair", "skill", "samsung", "lg", "biostar", "zotac",
    "palit", "galax", "pny", "crucial", "adata", "teamgroup",
}


def _numeric_token_present(token: str, title_words: set) -> bool:
    """True if `token` (e.g. '6000') appears as a whole word OR as part of
    a merged word (e.g. '6000mhz') in the title."""
    return any(token in w for w in title_words)


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def pick_best_match(results: list, part_key: str, min_similarity: float = 0.5):
    """
    Returns the single best-matching result dict, or None if nothing clears
    the bar (better to show "no match found" than a wrong part).

    HARD GATES (all must pass, in order):
      1. Every digit-containing token in the target (model numbers,
         capacities, DDR generation) must appear in the candidate title —
         as a whole word or merged into one (e.g. "6000mhz").
      2. Distinguishing suffixes (XT/Ti/Super/GRE/Plus) must match exactly
         on both sides — "RX 9070" must never match "RX 9070 XT".
      3. If the target names a specific brand (MSI, Asus, Gigabyte, etc.),
         the title must contain that same brand word — prevents a same-tier,
         different-manufacturer mismatch (e.g. MSI board matching an Asus
         listing purely because the chipset number lined up).
    """
    if not results:
        return None

    target = _normalize(part_key)
    target_words = set(target.split())
    required_numeric_tokens = {w for w in target_words if any(c.isdigit() for c in w)}
    target_brand_words = target_words & BRAND_KEYWORDS

    scored = []
    for r in results:
        title = _normalize(r["title"])
        title_words = set(title.split())

        if not all(_numeric_token_present(t, title_words) for t in required_numeric_tokens):
            continue

        target_suffixes = target_words & DISTINGUISHING_SUFFIXES
        title_suffixes = title_words & DISTINGUISHING_SUFFIXES
        if target_suffixes != title_suffixes:
            continue

        if target_brand_words and not target_brand_words.issubset(title_words):
            continue

        effective_title_words = set(title_words)
        for canonical, alias in BRAND_ALIASES.items():
            if alias in title_words:
                effective_title_words.add(canonical)

        ratio = difflib.SequenceMatcher(None, target, title).ratio()
        overlap = len(target_words & effective_title_words) / max(len(target_words), 1)
        combined = (overlap * 0.75) + (ratio * 0.25)
        scored.append((combined, r))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_result = scored[0]
    if best_score < min_similarity:
        return None
    return best_result


def build_dashboard(records: list) -> list:
    """
    records: list of dicts like:
      {"part_key", "category", "subcategory", "retailer", "title", "price",
       "url", "status", "stock_status", "stock_qty"}

    Returns dashboard-ready dicts, each with a "best_stock_status" /
    "best_stock_qty" for the cheapest offer, and per-offer stock info too
    (so the "compare N more offers" list can show stock per retailer).
    """
    grouped = {}
    for r in records:
        if r["status"] != "OK":
            continue
        key = r["part_key"]
        grouped.setdefault(key, {
            "part_key": key,
            "category": r["category"],
            "subcategory": r.get("subcategory"),
            "offers": [],
        })
        grouped[key]["offers"].append({
            "retailer": r["retailer"],
            "price": r["price"],
            "url": r["url"],
            "title": r["title"],
            "stock_status": r.get("stock_status", "unknown"),
            "stock_qty": r.get("stock_qty"),
        })

    dashboard = []
    for entry in grouped.values():
        entry["offers"].sort(key=lambda o: o["price"])
        if not entry["offers"]:
            continue
        best = entry["offers"][0]
        dashboard.append({
            "part_key": entry["part_key"],
            "category": entry["category"],
            "subcategory": entry["subcategory"],
            "best_price": best["price"],
            "best_retailer": best["retailer"],
            "best_url": best["url"],
            "best_title": best["title"],
            "best_stock_status": best["stock_status"],
            "best_stock_qty": best["stock_qty"],
            "offers": entry["offers"],
        })

    dashboard.sort(key=lambda d: (d["category"], d["subcategory"] or "", d["part_key"]))
    return dashboard
