"""
Central configuration for the AU PC Part Price Tracker.

RETAILERS — one entry per store: how to build a search URL, and which
fetch engine to use.

  mode: "requests"   -> fast, plain HTTP GET (BeautifulSoup parses result).
                        Only viable for sites that don't block non-browser
                        clients outright.
  mode: "playwright"  -> real headless Chromium. Needed for sites that sit
                        behind Cloudflare-style bot protection, which blocks
                        plain HTTP clients at the connection/TLS level before
                        the page even loads — no header trick fixes that,
                        only a real browser engine has a shot.

These modes were decided from an actual diagnostic run, not guesswork:
Centre Com, Scorptec, PC Case Gear, and Computer Alliance all returned
HTTP 403 to a plain HTTP request (confirmed bot-blocked) — hence Playwright.
Mwave and Umart returned normal 200 responses to a plain request — hence
the faster "requests" mode is used for those two.

Even Playwright is not a guaranteed bypass — some Cloudflare configurations
(e.g. "Turnstile" interactive challenges) can still block headless browsers.
When that happens for a given retailer, main.py logs it clearly as
BOT_CHALLENGE rather than silently returning nothing, so you know it's a
site-level block and not a broken selector.

TRACKED_PARTS — the shopping list: canonical part name, category, and the
search query to use per retailer. Every retailer entry under the same part
is treated as "the same product" for price-comparison purposes.
"""

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

RETAILERS = {
    "Centre Com": {
        "mode": "playwright",  # confirmed 403 on plain requests
        "search_url": "https://www.centrecom.com.au/catalogsearch/result/?q={query}",
    },
    "Scorptec": {
        "mode": "playwright",  # confirmed 403 on plain requests
        "search_url": "https://www.scorptec.com.au/search?query={query}",
    },
    "Mwave": {
        "mode": "requests",  # confirmed 200 on plain requests
        "search_url": "https://www.mwave.com.au/searchresult/index/keyword/{query}",
    },
    "PC Case Gear": {
        "mode": "playwright",  # confirmed 403 on plain requests
        "search_url": "https://www.pccasegear.com/catalogsearch/result/?q={query}",
    },
    "Umart": {
        "mode": "requests",  # confirmed 200 on plain requests once the
        # correct URL was used — Umart runs its own platform, not Magento;
        # its real search endpoint is search.php?keywords=, not the
        # catalogsearch path used by the Magento-based stores above.
        "search_url": "https://www.umart.com.au/search.php?keywords={query}",
    },
    "Computer Alliance": {
        "mode": "playwright",  # confirmed 403 on plain requests
        "search_url": "https://www.computeralliance.com.au/search?search={query}",
    },
    "Amazon AU": {
        # Amazon uses its own (non-Cloudflare) but equally aggressive bot
        # detection. Playwright helps but expect a meaningfully higher
        # failure rate here than any of the AU specialist retailers.
        "mode": "playwright",
        "search_url": "https://www.amazon.com.au/s?k={query}",
    },
}

# ---------------------------------------------------------------------------
# Shopping list. Add/remove rows freely. `retailers` maps retailer name ->
# the search query string to send to that retailer for this exact part.
# Covers AM4/AM5/LGA1700/LGA1851 CPUs, RTX 40/50-series + Radeon RX 7000/
# 9000-series GPUs (AMD hasn't shipped a desktop RX 8000-series — that
# number was mobile-only; RDNA4 desktop is the RX 9000-series), and DDR4/
# DDR5 kits from 16GB to 128GB.
# ---------------------------------------------------------------------------
TRACKED_PARTS = [
    # --- CPU: AM4 ---
    {"part_key": "AMD Ryzen 5 5600", "category": "CPU", "socket": "AM4",
     "retailers": {"Centre Com": "ryzen 5 5600", "Umart": "ryzen 5 5600"}},
    {"part_key": "AMD Ryzen 7 5800X3D", "category": "CPU", "socket": "AM4",
     "retailers": {"Scorptec": "5800x3d", "PC Case Gear": "ryzen 7 5800x3d"}},

    # --- CPU: AM5 ---
    {"part_key": "AMD Ryzen 5 7600", "category": "CPU", "socket": "AM5",
     "retailers": {"Centre Com": "ryzen 5 7600", "Mwave": "ryzen 5 7600"}},
    {"part_key": "AMD Ryzen 7 7800X3D", "category": "CPU", "socket": "AM5",
     "retailers": {"Scorptec": "7800x3d", "Umart": "7800x3d"}},
    {"part_key": "AMD Ryzen 9 9950X3D", "category": "CPU", "socket": "AM5",
     "retailers": {"PC Case Gear": "ryzen 9 9950x3d", "Centre Com": "9950x3d"}},

    # --- CPU: LGA1700 ---
    {"part_key": "Intel Core i5-14600K", "category": "CPU", "socket": "LGA1700",
     "retailers": {"Centre Com": "i5-14600k", "Mwave": "i5 14600k"}},
    {"part_key": "Intel Core i7-14700K", "category": "CPU", "socket": "LGA1700",
     "retailers": {"Umart": "14700k", "Scorptec": "i7-14700k"}},

    # --- CPU: LGA1851 ---
    {"part_key": "Intel Core Ultra 7 265K", "category": "CPU", "socket": "LGA1851",
     "retailers": {"PC Case Gear": "core ultra 7 265k", "Centre Com": "ultra 7 265k"}},
    {"part_key": "Intel Core Ultra 9 285K", "category": "CPU", "socket": "LGA1851",
     "retailers": {"Scorptec": "core ultra 9 285k", "Umart": "ultra 9 285k"}},

    # --- GPU: RTX 40-series ---
    {"part_key": "NVIDIA RTX 4060", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rtx 4060", "Umart": "rtx 4060"}},
    {"part_key": "NVIDIA RTX 4070 Super", "category": "GPU", "socket": None,
     "retailers": {"PC Case Gear": "rtx 4070 super", "Scorptec": "rtx 4070 super"}},
    {"part_key": "NVIDIA RTX 4080 Super", "category": "GPU", "socket": None,
     "retailers": {"Computer Alliance": "rtx 4080 super", "Mwave": "rtx 4080 super"}},

    # --- GPU: RTX 50-series ---
    {"part_key": "NVIDIA RTX 5070", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rtx 5070", "PC Case Gear": "rtx 5070"}},
    {"part_key": "NVIDIA RTX 5080", "category": "GPU", "socket": None,
     "retailers": {"Scorptec": "rtx 5080", "Umart": "rtx 5080"}},

    # --- GPU: Radeon RX 7000-series ---
    {"part_key": "AMD Radeon RX 7800 XT", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rx 7800 xt", "Umart": "7800 xt"}},
    {"part_key": "AMD Radeon RX 7900 XTX", "category": "GPU", "socket": None,
     "retailers": {"Mwave": "rx 7900 xtx", "PC Case Gear": "rx 7900 xtx"}},

    # --- GPU: Radeon RX 9000-series ---
    {"part_key": "AMD Radeon RX 9070 XT", "category": "GPU", "socket": None,
     "retailers": {"Scorptec": "rx 9070 xt", "Computer Alliance": "rx 9070 xt"}},
    {"part_key": "AMD Radeon RX 9070", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rx 9070", "Umart": "rx 9070"}},

    # --- RAM: DDR4 (16GB-128GB range) ---
    {"part_key": "Corsair Vengeance LPX 16GB (2x8GB) DDR4 3200", "category": "RAM", "socket": None,
     "retailers": {"Umart": "vengeance lpx 16gb ddr4 3200", "PC Case Gear": "vengeance lpx 16gb ddr4 3200"}},
    {"part_key": "G.Skill Ripjaws V 32GB (2x16GB) DDR4 3600", "category": "RAM", "socket": None,
     "retailers": {"Centre Com": "ripjaws v 32gb ddr4 3600", "Scorptec": "ripjaws v 32gb ddr4 3600"}},

    # --- RAM: DDR5 (16GB-128GB range) ---
    {"part_key": "Corsair Vengeance 32GB (2x16GB) DDR5 6000", "category": "RAM", "socket": None,
     "retailers": {"Umart": "vengeance 32gb ddr5 6000", "PC Case Gear": "vengeance 32gb ddr5 6000"}},
    {"part_key": "G.Skill Trident Z5 64GB (2x32GB) DDR5 6000", "category": "RAM", "socket": None,
     "retailers": {"Scorptec": "trident z5 64gb ddr5 6000", "Centre Com": "trident z5 64gb ddr5 6000"}},
    {"part_key": "Kingston Fury Beast 128GB (2x64GB) DDR5 5600", "category": "RAM", "socket": None,
     "retailers": {"Mwave": "fury beast 128gb ddr5 5600", "Umart": "fury beast 128gb ddr5 5600"}},
]
