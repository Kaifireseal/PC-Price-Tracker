"""
Entry point for the daily scrape.

Run manually:
    cd option_b_python/scraper
    python main.py

Run automatically:
    see ../.github/workflows/scrape.yml — GitHub Actions runs this on a
    24-hour cron schedule for free.

Output:
    ../data/prices.json    <- consumed by the dashboard/index.html frontend
    ../data/history.json   <- daily price history per part/retailer, for graphs
    scrape_errors.log      <- one line per failure, for debugging
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
HISTORY_PATH = ROOT / "data" / "history.json"
DEBUG_PATH = ROOT / "debug_snippets.json"
LOG_PATH = ROOT / "scrape_errors.log"

MAX_HISTORY_DAYS = 370  # ~1 year + buffer, prevents unbounded file growth

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
                        "stock_status": None, "stock_qty": None,
                    })
                    continue

                records.append({
                    "part_key": part_key, "category": category, "subcategory": subcategory,
                    "retailer": retailer_name,
                    "title": match["title"], "price": match["price"],
                    "url": match["url"], "status": "OK",
                    "stock_status": match.get("stock_status", "unknown"),
                    "stock_qty": match.get("stock_qty"),
                })
                logger.info(
                    "OK: %s | %s | $%.2f | stock=%s | %s",
                    part_key, retailer_name, match["price"],
                    match.get("stock_status", "unknown"), match["title"],
                )

            except Exception as exc:
                status = "BOT_BLOCKED" if "BOT_CHALLENGE" in str(exc) or "403" in str(exc) else "ERROR"
                logger.error("FAILED (%s): %s | %s | %s", status, part_key, retailer_name, exc)
                records.append({
                    "part_key": part_key, "category": category, "subcategory": subcategory,
                    "retailer": retailer_name, "title": None,
                    "price": None, "url": None, "status": status,
                    "error": str(exc),
                    "stock_status": None, "stock_qty": None,
                })

            # Human-ish pacing between requests.
            time.sleep(random.uniform(2.5, 5.5))

    return records


def update_history(dashboard: list, history_path: Path, today: str) -> None:
    """
    Append today's price for each part/retailer to history.json.

    Structure:
        {
          "<part_key>": {
            "<retailer>": [ {"date": "YYYY-MM-DD", "price": 119.0}, ... ],
            "best": [ {"date": "YYYY-MM-DD", "price": 119.0}, ... ]
          },
          ...
        }

    "best" tracks the cheapest across retailers each day, so the graph
    can default to a single line without picking a retailer first.
    """
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read existing history.json (%s), starting fresh", exc)
            history = {}
    else:
        history = {}

    for part in dashboard:
        part_key = part["part_key"]
        history.setdefault(part_key, {})

        for offer in part.get("offers", []):
            retailer = offer["retailer"]
            price = offer.get("price")
            if price is None:
                continue

            series = history[part_key].setdefault(retailer, [])
            if series and series[-1]["date"] == today:
                series[-1]["price"] = price  # overwrite same-day re-run
            else:
                series.append({"date": today, "price": price})
            del series[:-MAX_HISTORY_DAYS]  # keep only the most recent N days

        best_price = part.get("best_price")
        if best_price is not None:
            best_series = history[part_key].setdefault("best", [])
            if best_series and best_series[-1]["date"] == today:
                best_series[-1]["price"] = best_price
            else:
                best_series.append({"date": today, "price": best_price})
            del best_series[:-MAX_HISTORY_DAYS]

    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    logger.info("Updated %s", history_path)


def main():
    logger.info("Starting daily scrape for %d parts...", len(TRACKED_PARTS))
    records = scrape_all()
    dashboard = build_dashboard(records)

    now = datetime.now(timezone.utc)
    output = {
        "generated_at": now.isoformat(),
        "currency": "AUD",
        "parts": dashboard,
        "raw_records": records,
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    update_history(dashboard, HISTORY_PATH, today=now.date().isoformat())

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
