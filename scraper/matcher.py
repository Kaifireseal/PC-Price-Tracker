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


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def pick_best_match(results: list, part_key: str, min_similarity: float = 0.35):
    """
    Returns the single best-matching result dict, or None if nothing clears
    the similarity bar (better to show "no match found" than a wrong part).
    """
    if not results:
        return None

    target = _normalize(part_key)
    scored = []
    for r in results:
        title = _normalize(r["title"])
        ratio = difflib.SequenceMatcher(None, target, title).ratio()
        # Bonus if every "word" in the part key appears somewhere in the title
        # (e.g. "7800x3d" and "ryzen" and "7" all present) — catches cases
        # where word order differs but it's clearly the same product.
        target_words = set(target.split())
        title_words = set(title.split())
        overlap = len(target_words & title_words) / max(len(target_words), 1)
        combined = (ratio * 0.5) + (overlap * 0.5)
        scored.append((combined, r))

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
