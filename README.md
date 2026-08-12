# AU PC Part Price Tracker

An automated price tracker for PC parts in the Australian market. A daily
scraper checks retailer prices for a curated list of parts and publishes
the results to a static dashboard — no backend, no database, hosted free
on GitHub Pages.

**Live dashboard:** _add your GitHub Pages URL here_

## What it does

- Tracks prices across multiple retailers for ~90+ parts spanning CPUs,
  GPUs, RAM, SSDs, motherboards, and monitors
- Runs automatically every 24 hours via GitHub Actions and commits the
  updated data back to the repo
- Detects stock status (in stock / out of stock / pre-order) on a
  best-effort basis from each retailer's page
- Logs daily prices over time, so each part has a price history graph
  (1 week to 1 year) viewable right on the dashboard
- Filters by category and subcategory, with search

## How it works

1. `scraper/main.py` runs once a day (via `.github/workflows/scrape.yml`)
2. For each tracked part, it searches each configured retailer, picks the
   best matching product, and records price + stock status
3. Results are written to `data/prices.json` (current snapshot) and
   appended to `data/history.json` (daily price history per part)
4. `dashboard/index.html` is a static page that reads both files directly
   — GitHub Pages serves it with zero server-side code

## Project structure

```
scraper/
├── config.py          # retailers + tracked parts — edit this to add/remove items
├── scrapers.py         # requests+BeautifulSoup engine, Playwright engine
├── matcher.py           # picks the right search result, builds the dashboard payload
├── main.py               # orchestrator — run this daily
└── requirements.txt

data/
├── prices.json          # current snapshot — read by the dashboard
└── history.json          # daily price history per part, powers the graph

dashboard/
└── index.html           # static Tailwind dashboard, no backend needed

.github/workflows/
└── scrape.yml            # cron job — runs main.py every 24h, commits updated data
```

## Running locally

```bash
cd scraper
pip install -r requirements.txt
python main.py
```

This regenerates `data/prices.json` and appends to `data/history.json`.
Open `dashboard/index.html` in a browser (or serve the repo root with any
static file server) to view the result locally.

## Adding or removing tracked parts

Edit `scraper/config.py` — each entry defines a part's category,
subcategory, and the search query to use per retailer. The scraper picks
up new entries automatically on its next run.

## Retailers

Currently tracks **Umart** and **MSY**, chosen for reliability — most
other major AU retailers block automated requests via Cloudflare or
similar WAF protection. Retailer coverage is expected to expand over
time.

## Roadmap

- GPU / CPU tier ratings (relative performance tiers alongside price)
- PWA support for install-to-homescreen
- Expanded retailer coverage

## Disclaimer

Prices and stock status are scraped automatically and may be out of date
or inaccurate. Always confirm the final price and stock on the retailer's
own site before purchasing.