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

Discord alerts (optional):
    Set a DISCORD_WEBHOOK_URL environment variable (as a GitHub Actions
    secret) to get pinged when a part hits an all-time low or drops
    sharply vs yesterday. If the variable isn't set, alerts are skipped
    silently — nothing breaks.
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import TRACKED_PARTS
from scrapers import fetch_search_results, DEBUG_SNIPPETS
from matcher import pick_best_match, build_dashboard

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "prices.json"
HISTORY_PATH = ROOT / "data" / "history.json"
DEBUG_PATH = ROOT / "debug_snippets.json"
LOG_PATH = ROOT / "scrape_errors.log"

MAX_HISTORY_DAYS = 370  # ~1 year + buffer, prevents unbounded file growth
BIG_DROP_THRESHOLD_PCT = 5.0  # daily drop % that counts as "worth alerting"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

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


def load_history(history_path: Path) -> dict:
    if not history_path.exists():
        return {}
    try:
        return json.loads(history_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read existing history.json (%s), starting fresh", exc)
        return {}


def evaluate_alerts(dashboard: list, history: dict) -> tuple:
    """
    Compares each part's current best_price against its EXISTING history
    (i.e. before today's price is appended) to find:
      - record_lows: today's price beats every price ever recorded before today
      - big_drops:   today's price is BIG_DROP_THRESHOLD_PCT% or more below yesterday's

    Must be called before update_history() mutates the history dict.
    """
    record_lows = []
    big_drops = []

    for part in dashboard:
        part_key = part["part_key"]
        today_price = part.get("best_price")
        if today_price is None:
            continue

        series = (history.get(part_key) or {}).get("best", [])
        if not series:
            continue  # no baseline yet, nothing to compare against

        prior_min = min(pt["price"] for pt in series)
        if today_price < prior_min:
            record_lows.append({
                "part_key": part_key, "price": today_price,
                "prior_min": prior_min, "retailer": part.get("best_retailer"),
                "url": part.get("best_url"),
            })

        yesterday_price = series[-1]["price"]
        if yesterday_price > 0 and today_price < yesterday_price:
            pct = ((yesterday_price - today_price) / yesterday_price) * 100
            if pct >= BIG_DROP_THRESHOLD_PCT:
                big_drops.append({
                    "part_key": part_key, "price": today_price,
                    "yesterday_price": yesterday_price, "pct": pct,
                    "retailer": part.get("best_retailer"), "url": part.get("best_url"),
                })

    return record_lows, big_drops


def send_discord_alerts(record_lows: list, big_drops: list) -> None:
    if not DISCORD_WEBHOOK_URL:
        logger.info("DISCORD_WEBHOOK_URL not set, skipping Discord alerts.")
        return
    if not record_lows and not big_drops:
        logger.info("No alert-worthy price changes today.")
        return

    embeds = []

    if record_lows:
        lines = [
            f"**{p['part_key']}** — ${p['price']:.2f} @ {p['retailer']} "
            f"(previous low ${p['prior_min']:.2f})\n{p['url']}"
            for p in sorted(record_lows, key=lambda x: x["price"])[:10]
        ]
        embeds.append({
            "title": f"🔥 {len(record_lows)} part(s) hit an all-time low",
            "description": "\n\n".join(lines),
            "color": 0xE89A5C,
        })

    if big_drops:
        lines = [
            f"**{p['part_key']}** — ${p['price']:.2f} @ {p['retailer']} "
            f"(-{p['pct']:.0f}% from ${p['yesterday_price']:.2f})\n{p['url']}"
            for p in sorted(big_drops, key=lambda x: -x["pct"])[:10]
        ]
        embeds.append({
            "title": f"📉 {len(big_drops)} big price drop(s) today",
            "description": "\n\n".join(lines),
            "color": 0x45D4B8,
        })

    try:
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"embeds": embeds},
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Sent Discord alert: %d record low(s), %d big drop(s)",
                    len(record_lows), len(big_drops))
    except requests.RequestException as exc:
        logger.error("Failed to send Discord alert: %s", exc)


def append_today_to_history(history: dict, dashboard: list, today: str) -> dict:
    """
    Appends today's price for each part/retailer to the history dict
    (mutates and returns it). Structure:
        {
          "<part_key>": {
            "<retailer>": [ {"date": "YYYY-MM-DD", "price": 119.0}, ... ],
            "best": [ {"date": "YYYY-MM-DD", "price": 119.0}, ... ]
          },
          ...
        }
    """
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
            del series[:-MAX_HISTORY_DAYS]

        best_price = part.get("best_price")
        if best_price is not None:
            best_series = history[part_key].setdefault("best", [])
            if best_series and best_series[-1]["date"] == today:
                best_series[-1]["price"] = best_price
            else:
                best_series.append({"date": today, "price": best_price})
            del best_series[:-MAX_HISTORY_DAYS]

    return history


def main():
    logger.info("Starting daily scrape for %d parts...", len(TRACKED_PARTS))
    records = scrape_all()
    dashboard = build_dashboard(records)

    now = datetime.now(timezone.utc)
    today = now.date().isoformat()

    output = {
        "generated_at": now.isoformat(),
        "currency": "AUD",
        "parts": dashboard,
        "raw_records": records,
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    # Load history BEFORE appending today's prices, so alerts compare
    # against yesterday/prior data rather than the just-written value.
    history = load_history(HISTORY_PATH)
    record_lows, big_drops = evaluate_alerts(dashboard, history)

    append_today_to_history(history, dashboard, today)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    logger.info("Updated %s", HISTORY_PATH)

    send_discord_alerts(record_lows, big_drops)

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
