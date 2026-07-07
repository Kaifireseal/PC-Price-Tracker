"""
Turns raw per-retailer search results into a clean, matched dataset.

Two jobs:
  1. pick_best_match() — a search page returns several products; this picks
     the one whose title most closely matches the part we're actually
     looking for (protects against e.g. a search for "7800X3D" returning a
     motherboard bundle as the first result).
  2. build_dashboard() — groups matched offers by part_key and works out the
     cheapest current price + the full comparison list, which is exactly the
     shape the HTML dashboard and JSON file expect.
"""

import difflib
import re

# Short suffix words that distinguish otherwise-identical model numbers
# (e.g. "RX 9070" vs "RX 9070 XT" share the number "9070" but are different
# cards). These must match on BOTH sides — present in target but missing
# from title, or vice versa, means it's a different SKU.
DISTINGUISHING_SUFFIXES = {"xt", "ti", "super", "gre", "plus"}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def pick_best_match(results: list, part_key: str, min_similarity: float = 0.55):
    """
    Returns the single best-matching result dict, or None if nothing clears
    the bar (better to show "no match found" than a wrong part).

    HARD GATE: every digit-containing token in the target (model numbers
    like "4070", "265k", "7800x3d"; capacities like "16gb"; DDR generation
    like "ddr5") must appear somewhere in the candidate title. Word-overlap
    alone was letting a completely different model through — e.g. "RTX 3060
    Ti" scoring as a match for a search for "RTX 4070 Super" purely because
    "nvidia" and "rtx" overlapped, even though the actual defining number
    (4070) was nowhere in the title. A wrong price is worse than a missing
    one for a price tracker, so this gate is intentionally strict.
    """
    if not results:
        return None

    target = _normalize(part_key)
    target_words = set(target.split())
    required_numeric_tokens = {w for w in target_words if any(c.isdigit() for c in w)}

    scored = []
    for r in results:
        title = _normalize(r["title"])
        title_words = set(title.split())

        if not required_numeric_tokens.issubset(title_words):
            continue  # missing a model number/capacity/DDR-gen — not the same product

        target_suffixes = target_words & DISTINGUISHING_SUFFIXES
        title_suffixes = title_words & DISTINGUISHING_SUFFIXES
        if target_suffixes != title_suffixes:
            continue  # e.g. target "RX 9070" vs title "RX 9070 XT" — different card

        ratio = difflib.SequenceMatcher(None, target, title).ratio()
        overlap = len(target_words & title_words) / max(len(target_words), 1)
        combined = (ratio * 0.5) + (overlap * 0.5)
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
      {"part_key", "category", "socket", "retailer", "title", "price", "url", "status"}

    Returns a list of dashboard-ready dicts:
      {
        "part_key", "category",
        "best_price", "best_retailer", "best_url",
        "offers": [{"retailer", "price", "url", "title"}, ...]  # sorted cheapest first
      }
    """
    grouped = {}
    for r in records:
        if r["status"] != "OK":
            continue
        key = r["part_key"]
        grouped.setdefault(key, {
            "part_key": key,
            "category": r["category"],
            "offers": [],
        })
        grouped[key]["offers"].append({
            "retailer": r["retailer"],
            "price": r["price"],
            "url": r["url"],
            "title": r["title"],
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
            "best_price": best["price"],
            "best_retailer": best["retailer"],
            "best_url": best["url"],
            "offers": entry["offers"],
        })

    dashboard.sort(key=lambda d: (d["category"], d["part_key"]))
    return dashboard
