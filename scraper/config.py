"""
Central configuration for the AU PC Part Price Tracker.

RETAILERS — one entry per store: how to build a URL, and which fetch
engine to use.

  mode: "requests"   -> fast, plain HTTP GET (BeautifulSoup parses result).
                        Only viable for sites that don't block non-browser
                        clients outright.
  mode: "playwright"  -> real headless Chromium. Needed for sites that sit
                        behind Cloudflare-style bot protection.

  url_mode: "search"  -> "search_url" is a template with {query}, filled in
                        per-part with a search term (e.g. "ryzen 5 7600").
  url_mode: "category" -> "search_url" is used AS-IS (no {query} filling).
                        Used for MSY, which doesn't have a simple search
                        endpoint we could confirm — instead we point
                        straight at MSY's stable category listing pages,
                        which already show every product + price in that
                        category. For these, the "query" value in
                        TRACKED_PARTS is a label into CATEGORY_URLS below.

CONFIRMED STATUS (from actual diagnostic runs):
  - Centre Com, Scorptec: confirmed blocked by Cloudflare's interactive
    "Turnstile" challenge even through Playwright. Expect BOT_BLOCKED most
    days — a genuinely hard wall, not a bug in this code.
  - Mwave: confirmed blocked by an AWS WAF JS challenge, also even through
    Playwright.
  - Umart, MSY: confirmed working reliably via plain "requests".

BRAND VISIBILITY: the actual matched product title (e.g. "Gigabyte Radeon
RX 9070 Gaming 16G OC") is what gets shown on the dashboard under each
part's generic name — brand/model comes through automatically from
whatever the real top-matching listing is, no extra config needed here.

TRACKED_PARTS — the shopping list: canonical part name, category, and the
search query (or MSY category label) to use per retailer. Every retailer
entry under the same part is treated as "the same product" for
price-comparison purposes.
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
        "mode": "playwright",
        "url_mode": "search",
        "search_url": "https://www.centrecom.com.au/catalogsearch/result/?q={query}",
    },
    "Scorptec": {
        "mode": "playwright",
        "url_mode": "search",
        "search_url": "https://www.scorptec.com.au/search?query={query}",
    },
    "Mwave": {
        "mode": "playwright",
        "url_mode": "search",
        "search_url": "https://www.mwave.com.au/searchresult/index/keyword/{query}",
    },
    "Umart": {
        "mode": "requests",
        "url_mode": "search",
        "search_url": "https://www.umart.com.au/search.php?keywords={query}",
    },
    "MSY": {
        "mode": "requests",
        "url_mode": "category",
        "search_url": None,
    },
}

# MSY category listing pages, verified live. Referenced by label from
# TRACKED_PARTS entries below.
CATEGORY_URLS = {
    "amd_cpu": "https://www.msy.com.au/pc-parts/computer-parts/cpu-processors/amd-cpu-646",
    "intel_cpu": "https://www.msy.com.au/pc-parts/computer-parts/cpu-processors/intel-cpu-645",
    "gpu_rtx_4060": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu/geforce-rtx-4060-1141",
    "gpu_rtx_5060": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu/geforce-rtx-5060-1396",
    "gpu_rtx_5060ti": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu/geforce-rtx-5060-ti-1395",
    "gpu_rtx_5070": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu/geforce-rtx-5070-1388",
    "gpu_rtx_5080": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu/geforce-rtx-5080-1385",
    "gpu_rtx_5090": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu/geforce-rtx-5090-1386",
    "gpu_rx_7900xtx": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu/radeon-rx-7900-xtx-1124",
    "gpu_rx_9060xt": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu/radeon-rx-9060-xt-1398",
    # Fallback for models without a confirmed sub-category ID (RTX 5070 Ti,
    # RX 7600/7700 XT/7900 GRE/7900 XT, RX 9070/9070 XT) — lists everything,
    # but matcher.py's hard model-number + suffix gate (fixed after the
    # earlier RTX-3060-Ti false-match bug) keeps this safe from wrong-model
    # mismatches even on a big unfiltered page.
    "gpu_all": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu-610",
    "ddr4_ram": "https://www.msy.com.au/pc-parts/computer-parts/memory-ram/ddr4-ram-659",
    "ddr5_ram": "https://www.msy.com.au/pc-parts/computer-parts/memory-ram/ddr5-ram-1085",
}

# ---------------------------------------------------------------------------
# Shopping list.
#
# CPU coverage: AM4, AM5, LGA1700, LGA1851 — expanded lineup covering both
# AMD Ryzen and Intel, budget through flagship.
#
# GPU coverage: NVIDIA RTX 30/40/50-series and AMD Radeon RX 7000/9000-series.
#
# RAM coverage: DDR4/DDR5, 16GB-128GB.
# ---------------------------------------------------------------------------
TRACKED_PARTS = [
    # --- CPU: AM4 ---
    {"part_key": "AMD Ryzen 5 5500", "category": "CPU", "socket": "AM4",
     "retailers": {"Umart": "ryzen 5 5500", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 5600", "category": "CPU", "socket": "AM4",
     "retailers": {"Centre Com": "ryzen 5 5600", "Umart": "ryzen 5 5600", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 5700X3D", "category": "CPU", "socket": "AM4",
     "retailers": {"Umart": "5700x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 5800X3D", "category": "CPU", "socket": "AM4",
     "retailers": {"Scorptec": "5800x3d", "Umart": "5800x3d", "MSY": "amd_cpu"}},

    # --- CPU: AM5 ---
    {"part_key": "AMD Ryzen 5 7500F", "category": "CPU", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 7500f", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 7600", "category": "CPU", "socket": "AM5",
     "retailers": {"Centre Com": "ryzen 5 7600", "Mwave": "ryzen 5 7600", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 9600X", "category": "CPU", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 9600x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 7700X", "category": "CPU", "socket": "AM5",
     "retailers": {"Umart": "ryzen 7 7700x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 7800X3D", "category": "CPU", "socket": "AM5",
     "retailers": {"Scorptec": "7800x3d", "Umart": "7800x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 9800X3D", "category": "CPU", "socket": "AM5",
     "retailers": {"Centre Com": "9800x3d", "Umart": "9800x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 7900X", "category": "CPU", "socket": "AM5",
     "retailers": {"Umart": "ryzen 9 7900x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 7950X", "category": "CPU", "socket": "AM5",
     "retailers": {"Centre Com": "ryzen 9 7950x", "Umart": "ryzen 9 7950x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9900X3D", "category": "CPU", "socket": "AM5",
     "retailers": {"Umart": "9900x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9950X3D", "category": "CPU", "socket": "AM5",
     "retailers": {"Centre Com": "9950x3d", "MSY": "amd_cpu"}},

    # --- CPU: LGA1700 (Intel, older/budget-friendly through flagship) ---
    {"part_key": "Intel Core i5-13400F", "category": "CPU", "socket": "LGA1700",
     "retailers": {"Umart": "i5-13400f", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core i5-14400F", "category": "CPU", "socket": "LGA1700",
     "retailers": {"Centre Com": "i5-14400f", "Umart": "i5-14400f", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core i5-14600K", "category": "CPU", "socket": "LGA1700",
     "retailers": {"Centre Com": "i5-14600k", "Mwave": "i5 14600k", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core i7-14700K", "category": "CPU", "socket": "LGA1700",
     "retailers": {"Umart": "14700k", "Scorptec": "i7-14700k", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core i9-14900K", "category": "CPU", "socket": "LGA1700",
     "retailers": {"Centre Com": "i9-14900k", "Umart": "14900k", "MSY": "intel_cpu"}},

    # --- CPU: LGA1851 (Intel current-gen) ---
    {"part_key": "Intel Core Ultra 5 245K", "category": "CPU", "socket": "LGA1851",
     "retailers": {"Umart": "ultra 5 245k", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core Ultra 7 265K", "category": "CPU", "socket": "LGA1851",
     "retailers": {"Centre Com": "ultra 7 265k", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core Ultra 9 285K", "category": "CPU", "socket": "LGA1851",
     "retailers": {"Scorptec": "core ultra 9 285k", "Umart": "ultra 9 285k", "MSY": "intel_cpu"}},

    # --- GPU: RTX 30/40-series (kept as budget/mid reference points) ---
    {"part_key": "NVIDIA RTX 3060", "category": "GPU", "socket": None,
     "retailers": {"Umart": "rtx 3060", "MSY": "gpu_all"}},
    {"part_key": "NVIDIA RTX 4060", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rtx 4060", "Umart": "rtx 4060", "MSY": "gpu_rtx_4060"}},
    {"part_key": "NVIDIA RTX 4070", "category": "GPU", "socket": None,
     "retailers": {"Umart": "rtx 4070", "MSY": "gpu_all"}},
    {"part_key": "NVIDIA RTX 4070 Ti Super", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rtx 4070 ti super", "Umart": "rtx 4070 ti super", "MSY": "gpu_all"}},

    # --- GPU: RTX 50-series (full lineup) ---
    {"part_key": "NVIDIA RTX 5060", "category": "GPU", "socket": None,
     "retailers": {"Umart": "rtx 5060", "MSY": "gpu_rtx_5060"}},
    {"part_key": "NVIDIA RTX 5060 Ti", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rtx 5060 ti", "Umart": "rtx 5060 ti", "MSY": "gpu_rtx_5060ti"}},
    {"part_key": "NVIDIA RTX 5070", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rtx 5070", "MSY": "gpu_rtx_5070"}},
    {"part_key": "NVIDIA RTX 5070 Ti", "category": "GPU", "socket": None,
     "retailers": {"Umart": "rtx 5070 ti", "Scorptec": "rtx 5070 ti", "MSY": "gpu_all"}},
    {"part_key": "NVIDIA RTX 5080", "category": "GPU", "socket": None,
     "retailers": {"Scorptec": "rtx 5080", "Umart": "rtx 5080", "MSY": "gpu_rtx_5080"}},
    {"part_key": "NVIDIA RTX 5090", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rtx 5090", "Umart": "rtx 5090", "MSY": "gpu_rtx_5090"}},

    # --- GPU: Radeon RX 7000-series (full lineup) ---
    {"part_key": "AMD Radeon RX 7600", "category": "GPU", "socket": None,
     "retailers": {"Umart": "rx 7600", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7700 XT", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rx 7700 xt", "Umart": "rx 7700 xt", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7800 XT", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rx 7800 xt", "Umart": "7800 xt", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7900 GRE", "category": "GPU", "socket": None,
     "retailers": {"Umart": "rx 7900 gre", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7900 XT", "category": "GPU", "socket": None,
     "retailers": {"Scorptec": "rx 7900 xt", "Umart": "rx 7900 xt", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7900 XTX", "category": "GPU", "socket": None,
     "retailers": {"Mwave": "rx 7900 xtx", "MSY": "gpu_rx_7900xtx"}},

    # --- GPU: Radeon RX 9000-series ---
    {"part_key": "AMD Radeon RX 9070", "category": "GPU", "socket": None,
     "retailers": {"Centre Com": "rx 9070", "Umart": "rx 9070", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 9070 XT", "category": "GPU", "socket": None,
     "retailers": {"Scorptec": "rx 9070 xt", "MSY": "gpu_all"}},

    # --- RAM: DDR4 (16GB-128GB range) ---
    {"part_key": "Corsair Vengeance LPX 16GB (2x8GB) DDR4 3200", "category": "RAM", "socket": None,
     "retailers": {"Umart": "vengeance lpx 16gb ddr4 3200", "MSY": "ddr4_ram"}},
    {"part_key": "G.Skill Ripjaws V 32GB (2x16GB) DDR4 3600", "category": "RAM", "socket": None,
     "retailers": {"Centre Com": "ripjaws v 32gb ddr4 3600", "Scorptec": "ripjaws v 32gb ddr4 3600", "MSY": "ddr4_ram"}},

    # --- RAM: DDR5 (16GB-128GB range) ---
    {"part_key": "Corsair Vengeance 32GB (2x16GB) DDR5 6000", "category": "RAM", "socket": None,
     "retailers": {"Umart": "vengeance 32gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "G.Skill Trident Z5 64GB (2x32GB) DDR5 6000", "category": "RAM", "socket": None,
     "retailers": {"Scorptec": "trident z5 64gb ddr5 6000", "Centre Com": "trident z5 64gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "Kingston Fury Beast 128GB (2x64GB) DDR5 5600", "category": "RAM", "socket": None,
     "retailers": {"Mwave": "fury beast 128gb ddr5 5600", "Umart": "fury beast 128gb ddr5 5600", "MSY": "ddr5_ram"}},
]
