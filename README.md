# AU PC Part Price Tracker — Website version

## Why this replaced the Google Sheets version
Testing the Apps Script version turned up a hard limit: 4 of the 6 target
retailers (Centre Com, Scorptec, PC Case Gear, Computer Alliance) actively
block plain HTTP requests with a 403 — they sit behind Cloudflare-style bot
protection that checks the connection itself (server IP reputation, TLS/
browser fingerprint) before your request headers are even read. Apps
Script's `UrlFetchApp` can't get past that; no regex or header fix changes
it. Mwave and Umart, by contrast, returned normal responses to a plain
request — those two didn't need a browser at all.

This version fixes that by using **Playwright** (a real headless Chromium
browser) for the four blocked retailers, since a genuine browser
fingerprint has a real — though not guaranteed — chance of getting past
that kind of protection. Mwave and Umart still use fast plain HTTP requests
since they don't need the extra weight.

**Being upfront about the ceiling here:** some Cloudflare configurations use
an interactive "Turnstile" challenge that can still detect and block
headless browsers, even with the stealth tweaks included
(`scrapers.py` hides the most obvious "this is automation" signal, but
that's a basic measure, not a full bypass suite). When a retailer blocks
even Playwright, `main.py` logs it distinctly as `BOT_BLOCKED` in
`scrape_errors.log` and in `prices.json`'s `raw_records`, rather than
pretending it's a parsing bug — so you'll always know which failures are
"needs a selector fix" versus "this site is actively resisting automation
and may need a paid scraping-proxy service (ScraperAPI, ScrapingBee,
ZenRows) if full coverage matters enough to you to pay for it."

## Architecture
```
option_b_python/
├── scraper/
│   ├── config.py        # retailers + tracked parts (edit this to add/remove items)
│   ├── scrapers.py       # requests+BeautifulSoup engine, Playwright engine
│   ├── matcher.py        # picks the right search result, builds comparisons
│   ├── main.py            # orchestrator — run this daily
│   └── requirements.txt
├── data/
│   └── prices.json       # output — the dashboard reads this file
├── dashboard/
│   └── index.html         # static Tailwind dashboard, no backend needed
└── .github/workflows/
    └── scrape.yml          # cron job — runs main.py every 24h, commits prices.json
```

## How the 24-hour loop works
GitHub Actions has a free tier that includes scheduled ("cron") jobs on
public repos (2,000 free minutes/month on private repos too, plenty for a
job that finishes in 1-3 minutes). `.github/workflows/scrape.yml` is set to
`cron: '0 20 * * *'`, which runs once a day. Each run:
1. Spins up a fresh Ubuntu VM.
2. Installs Python deps + a headless Chromium (for the Amazon/Playwright path).
3. Runs `main.py`, which scrapes every retailer for every part in
   `TRACKED_PARTS` and writes `data/prices.json`.
4. Commits that updated JSON file straight back into your repo.

Because the dashboard is a static page that fetches `../data/prices.json`,
the moment the bot commits new data, the live site (see hosting below)
reflects it — no server to keep running, no always-on process, fully free.

## Step-by-step setup

### 1. Create the repo
1. Create a new **GitHub repository** (public or private both work).
2. Copy this entire `option_b_python/` folder structure into the repo root
   (or into a subfolder — just update the `working-directory` paths in
   `scrape.yml` to match).
3. Commit and push.

### 2. Enable Actions + permissions
1. In the repo: **Settings → Actions → General → Workflow permissions** →
   select **"Read and write permissions"**. This lets the workflow commit
   `prices.json` back to the repo.
2. Go to the **Actions** tab, find "Daily AU PC Part Price Scrape", and
   click **Run workflow** to trigger it manually the first time and confirm
   it works end-to-end.

### 3. Customise what gets tracked
Open `scraper/config.py` and edit `TRACKED_PARTS`. Each entry needs:
```python
{
    "part_key": "AMD Ryzen 7 7800X3D",   # canonical name shown on the dashboard
    "category": "CPU",                    # CPU / GPU / RAM
    "socket": "AM5",                      # optional, for your own reference
    "retailers": {
        "Centre Com": "7800x3d",          # retailer name -> search query
        "Scorptec": "7800x3d",
    },
},
```
The `retailers` dict must use retailer names that also exist in the
`RETAILERS` dict above it (that's where the CSS selectors live).

### 4. Run it locally first (recommended before relying on Actions)
```bash
cd option_b_python/scraper
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium     # only needed once, for the Amazon AU path
python main.py
```
Check `../data/prices.json` was written and `scrape_errors.log` for any
`NO MATCH` / `FAILED` lines — that tells you immediately if a selector in
`config.py` needs adjusting for a retailer's current page layout.

### 5. Host the dashboard for free (GitHub Pages)
1. Repo **Settings → Pages** → Source: **Deploy from a branch** → pick
   `main` and `/ (root)` (or `/option_b_python` if you nested the folder).
2. Your dashboard will be live at
   `https://<your-username>.github.io/<repo-name>/dashboard/`.
3. Because GitHub Pages serves straight from the repo, every time the daily
   Action commits a fresh `prices.json`, the live page updates within
   minutes — no redeploy step needed.

### Alternative: PythonAnywhere (if you'd rather not use GitHub Actions)
1. Create a free account at pythonanywhere.com.
2. Upload the `scraper/` folder (Files tab, or `git clone` your repo via
   their Bash console).
3. `pip install -r requirements.txt --user` in a Bash console.
4. **Tasks** tab → add a **Daily Task** → command:
   `python3.x /home/yourusername/option_b_python/scraper/main.py`
   (free accounts get one scheduled task, run once a day — exactly what you need).
5. Point the dashboard's `fetch()` at wherever `prices.json` ends up (e.g.
   serve it via PythonAnywhere's static files, or have the task `git push`
   it to a Pages-hosted repo like in the GitHub option above).
   Note: Playwright/Chromium is heavy for PythonAnywhere's free tier — if
   you go this route, consider dropping the Amazon AU entry and sticking to
   the `requests`-based retailers.

## Anti-scraping notes specific to this option
- **Parsing is heuristic, not selector-based.** Instead of hard-coded CSS
  class names (fragile — breaks the moment a site redesigns, and requires
  guessing markup you haven't actually verified), `scrapers.py` finds
  products by shape: a link with plausible title-length text, near a
  `$`-formatted price in a nearby container. This is more resilient to
  layout changes, at the cost of occasionally picking up an unrelated
  price; `matcher.py`'s similarity scoring is the safety net that filters
  those out by comparing candidate titles against the part you're actually
  looking for.
- **Two failure types, logged distinctly.** `ERROR` means something
  ordinary went wrong (timeout, network blip, unexpected page).
  `BOT_BLOCKED` means the site's bot protection rejected the request
  outright (an HTTP 403, or a detected Cloudflare-style challenge page) —
  no amount of retrying fixes that on its own.
- **Rotate nothing aggressively; just look like a normal client.** The
  `COMMON_HEADERS` in `config.py` set a realistic desktop Chrome
  `User-Agent` and `en-AU` Accept-Language for the plain-HTTP retailers.
  For the Playwright-driven retailers, a real browser engine handles this
  more thoroughly by default.
- **Respect rate limits.** `main.py` scrapes retailers sequentially with
  built-in retry/backoff; it does not fire concurrent requests at a single
  site. This is deliberately conservative — the goal is a stable daily job,
  not the fastest possible scrape.
- **Amazon AU and any retailer marked `BOT_BLOCKED` after a Playwright
  attempt** are the realistic limit of what a free, self-hosted approach
  can do. The durable fix at that point is either a paid scraping-proxy API
  (which handles the harder bypass work server-side) or, for Amazon
  specifically, its official Product Advertising API — both more stable
  long-term than an arms race against evolving bot detection.
- **Check each retailer's Terms of Service before relying on this
  long-term.** This project is intended for personal, low-frequency
  (once-daily) price comparison, not redistribution or commercial resale of
  the scraped data.
