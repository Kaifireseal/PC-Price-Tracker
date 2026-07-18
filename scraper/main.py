"""
Entry point for the daily scrape.

Run manually:
    cd option_b_python/scraper
    python main.py

Run automatically:
    see ../.github/workflows/scrape.yml — GitHub Actions runs this on a
    24-hour cron schedule for free.

Output:
    ../data/prices.json   <- consumed by the dashboard/index.html frontend
    scrape_errors.log     <- one line per failure, for debugging selectors
"""

import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from config import TRACKED_PARTS
from scrapers import fetch_search_results, DEBUG_SNIPPETS
from matcher import pick_best_match, build_dashboard

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "prices.json"
DEBUG_PATH = ROOT / "debug_snippets.json"
LOG_PATH = ROOT / "scrape_errors.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("main")


def scrape_all() -> list:
    records = []

    for part in TRACKED_PARTS:
        part_key = part["part_key"]
        category = part["category"]
        subcategory = part.get("subcategory")

        for retailer_name, query in part["retailers"].items():
            try:
                results = fetch_search_results(retailer_name, query)
                match = pick_best_match(results, part_key)

                if match is None:
                    logger.warning(
                        "NO MATCH: %s | %s | query='%s' (got %d raw results)",
                        part_key, retailer_name, query, len(results),
                    )
                    records.append({
                        "part_key": part_key, "category": category, "subcategory": subcategory,
                        "retailer": retailer_name, "title": None,
                        "price": None, "url": None, "status": "NO_MATCH",
                    })
                    continue

                records.append({
                    "part_key": part_key, "category": category, "subcategory": subcategory,
                    "retailer": retailer_name,
                    "title": match["title"], "price": match["price"],
                    "url": match["url"], "status": "OK",
                })
                logger.info(
                    "OK: %s | %s | $%.2f | %s",
                    part_key, retailer_name, match["price"], match["title"],
                )

            except Exception as exc:
                status = "BOT_BLOCKED" if "BOT_CHALLENGE" in str(exc) or "403" in str(exc) else "ERROR"
                logger.error("FAILED (%s): %s | %s | %s", status, part_key, retailer_name, exc)
                records.append({
                    "part_key": part_key, "category": category, "subcategory": subcategory,
                    "retailer": retailer_name, "title": None,
                    "price": None, "url": None, "status": status,
                    "error": str(exc),
                })

            # Human-ish pacing between requests. Bot-scoring systems (Mwave's
            # AWS WAF included) weigh request rhythm, not just headers — a
            # burst of perfectly-timed requests is itself a signal. This
            # slows the daily run down but meaningfully softens that signal.
            time.sleep(random.uniform(2.5, 5.5))

    return records


def main():
    logger.info("Starting daily scrape for %d parts...", len(TRACKED_PARTS))
    records = scrape_all()
    dashboard = build_dashboard(records)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "currency": "AUD",
        "parts": dashboard,
        "raw_records": records,  # kept for debugging / auditing failed scrapes
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    if DEBUG_SNIPPETS:
        DEBUG_PATH.write_text(json.dumps(DEBUG_SNIPPETS, indent=2), encoding="utf-8")
        logger.info("Wrote debug snippets for %d retailer(s) to %s", len(DEBUG_SNIPPETS), DEBUG_PATH)

    ok_count = sum(1 for r in records if r["status"] == "OK")
    logger.info(
        "Done. %d/%d fetches succeeded. Wrote %s",
        ok_count, len(records), DATA_PATH,
    )


if __name__ == "__main__":
    main()
