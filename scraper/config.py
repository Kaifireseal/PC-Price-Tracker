"""
Central configuration for the AU PC Part Price Tracker.

RETAILERS — one entry per store: how to build a URL, and which fetch
engine to use.

  mode: "requests"   -> fast, plain HTTP GET (BeautifulSoup parses result).
  mode: "playwright"  -> real headless Chromium, for sites that block plain
                        HTTP clients at the connection level.

  url_mode: "search"  -> "search_url" is a template with {query}.
  url_mode: "category" -> "search_url" is used AS-IS. Used for MSY, which
                        doesn't have a simple search endpoint — instead we
                        point straight at MSY's stable category listing
                        pages. The "query" value in TRACKED_PARTS is then a
                        label into CATEGORY_URLS below.

CONFIRMED STATUS (from actual diagnostic runs):
  - Centre Com, Scorptec: confirmed blocked by Cloudflare's interactive
    "Turnstile" challenge even through Playwright. Expect BOT_BLOCKED most
    days — a genuinely hard wall, not a bug in this code.
  - Mwave: confirmed blocked by an AWS WAF JS challenge, also even through
    Playwright.
  - Umart, MSY: confirmed working reliably via plain "requests".

SUBCATEGORY: every part carries a "subcategory" alongside "category" —
socket for CPUs/motherboards (AM4/AM5/LGA1700/LGA1851), generation for GPUs
(RTX 30/40/50-series, RX 7000/9000-series), DDR generation for RAM,
capacity for SSDs, and display type for monitors. This drives the
dashboard's second-level filter pills.

MULTIPLE BRANDS PER TIER: many capacity/chip tiers now have 2-3 different
brands tracked as separate part_key entries (e.g. three different 32GB
DDR5 6000 kits, three different RX 7800 XT AIB cards). Each one still only
returns its single best real-world match per retailer — the "multiple
brands visible" comes from these being separate tracked items that each
show up as their own card, not from one query returning several results.

TRACKED_PARTS — the shopping list: canonical part name, category,
subcategory, and the search query (or MSY category label) to use per
retailer.
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
    "gpu_all": "https://www.msy.com.au/pc-parts/computer-parts/graphics-cards-gpu-610",
    "ddr4_ram": "https://www.msy.com.au/pc-parts/computer-parts/memory-ram/ddr4-ram-659",
    "ddr5_ram": "https://www.msy.com.au/pc-parts/computer-parts/memory-ram/ddr5-ram-1085",
    "mobo_amd_am4": "https://www.msy.com.au/pc-parts/computer-parts/motherboards/amd-am4-966",
    "mobo_amd_am5": "https://www.msy.com.au/pc-parts/computer-parts/motherboards/amd-am5-1115",
    "mobo_intel_lga1700": "https://www.msy.com.au/pc-parts/computer-parts/motherboards/intel-lga-1700-1086",
    "mobo_intel_lga1851": "https://www.msy.com.au/pc-parts/computer-parts/motherboards/intel-lga-1851-1380",
    "monitor_general": "https://www.msy.com.au/pc-parts/peripherals/monitors/monitors-680",
    "monitor_4k": "https://www.msy.com.au/pc-parts/peripherals/monitors/4k-uhd-monitors-1109",
    "monitor_oled": "https://www.msy.com.au/pc-parts/peripherals/monitors/oled-monitors-1206",
    "ssd": "https://www.msy.com.au/pc-parts/storage-devices/ssd-hard-drives-580",
}

TRACKED_PARTS = [
    # ============================== CPU ==============================
    # --- AM4 ---
    {"part_key": "AMD Ryzen 5 3600", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "ryzen 5 3600", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 5500", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "ryzen 5 5500", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 5600", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Centre Com": "ryzen 5 5600", "Umart": "ryzen 5 5600", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 5600X", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Centre Com": "ryzen 5 5600x", "Umart": "ryzen 5 5600x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 5700X", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "5700x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 5800X3D", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Scorptec": "5800x3d", "Umart": "5800x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 5900X", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "ryzen 9 5900x", "MSY": "amd_cpu"}},

    # --- AM5 ---
    {"part_key": "AMD Ryzen 5 8400F", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 8400f", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 7500F", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 7500f", "MSY": "amd_cpu"}},
     {"part_key": "AMD Ryzen 5 7500X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 7500x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 7600", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Centre Com": "ryzen 5 7600", "Mwave": "ryzen 5 7600", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 7600X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Centre Com": "ryzen 5 7600x", "Mwave": "ryzen 5 7600x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 5 9600X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 9600x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 8700F", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 7 8700f", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 7700X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 7 7700x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 7800X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Scorptec": "7800x3d", "Umart": "7800x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 7 9800X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Centre Com": "9800x3d", "Umart": "9800x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 7900X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 9 7900x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 7950X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Centre Com": "ryzen 9 7950x", "Umart": "ryzen 9 7950x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9900X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "9900x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9950X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 9 9950x", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9950X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Centre Com": "9950x3d", "MSY": "amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9950X3D2", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Centre Com": "9950x3d2", "MSY": "amd_cpu"}},

    # --- LGA1700 ---
    {"part_key": "Intel Core i5-13400F", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "i5-13400f", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core i5-14400F", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Centre Com": "i5-14400f", "Umart": "i5-14400f", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core i5-12400F", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Centre Com": "i5-12400f", "Mwave": "i5 12400f", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core i7-14700K", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "14700k", "Scorptec": "i7-14700k", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core i9-14900K", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Centre Com": "i9-14900k", "Umart": "14900k", "MSY": "intel_cpu"}},

    # --- LGA1851 ---
    {"part_key": "Intel Core Ultra 5 245K", "category": "CPU", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Umart": "ultra 5 245k", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core Ultra 7 265K", "category": "CPU", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Centre Com": "ultra 7 265k", "MSY": "intel_cpu"}},
    {"part_key": "Intel Core Ultra 9 285K", "category": "CPU", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Scorptec": "core ultra 9 285k", "Umart": "ultra 9 285k", "MSY": "intel_cpu"}},

    # ============================== GPU ==============================
    # --- RTX 30-series ---
    {"part_key": "NVIDIA RTX 3060", "category": "GPU", "subcategory": "RTX 30-series", "socket": None,
     "retailers": {"Umart": "rtx 3060", "MSY": "gpu_all"}},

    # --- RTX 40-series ---
    {"part_key": "NVIDIA RTX 4060", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Centre Com": "rtx 4060", "Umart": "rtx 4060", "MSY": "gpu_rtx_4060"}},
    {"part_key": "NVIDIA RTX 4060 Ti", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Umart": "rtx 4060 ti", "MSY": "gpu_all"}},
    {"part_key": "NVIDIA RTX 4070", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Umart": "rtx 4070", "MSY": "gpu_all"}},
    {"part_key": "NVIDIA RTX 4070 Ti Super", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Centre Com": "rtx 4070 ti super", "Umart": "rtx 4070 ti super", "MSY": "gpu_all"}},
    {"part_key": "NVIDIA RTX 4090", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Centre Com": "rtx 4090", "Umart": "rtx 4090", "MSY": "gpu_all"}},

    # --- RTX 50-series ---
    {"part_key": "NVIDIA RTX 5060", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Umart": "rtx 5060", "MSY": "gpu_rtx_5060"}},
    {"part_key": "NVIDIA RTX 5060 Ti", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Centre Com": "rtx 5060 ti", "Umart": "rtx 5060 ti", "MSY": "gpu_rtx_5060ti"}},
    {"part_key": "NVIDIA RTX 5070", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Centre Com": "rtx 5070", "MSY": "gpu_rtx_5070"}},
    {"part_key": "NVIDIA RTX 5070 Ti", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Umart": "rtx 5070 ti", "Scorptec": "rtx 5070 ti", "MSY": "gpu_all"}},
    {"part_key": "NVIDIA RTX 5080", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Scorptec": "rtx 5080", "Umart": "rtx 5080", "MSY": "gpu_rtx_5080"}},
    {"part_key": "NVIDIA RTX 5090", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Centre Com": "rtx 5090", "Umart": "rtx 5090", "MSY": "gpu_rtx_5090"}},

    # --- RX 7000-series (with brand variants) ---
    {"part_key": "AMD Radeon RX 7600", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Umart": "rx 7600", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7700 XT", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Centre Com": "rx 7700 xt", "Umart": "rx 7700 xt", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7800 XT", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Centre Com": "rx 7800 xt", "Umart": "7800 xt", "MSY": "gpu_all"}},
    {"part_key": "Sapphire Pulse RX 7800 XT", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Umart": "sapphire pulse rx 7800 xt", "MSY": "gpu_all"}},
    {"part_key": "PowerColor Fighter RX 7800 XT", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Umart": "powercolor fighter rx 7800 xt", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7900 GRE", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Umart": "rx 7900 gre", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7900 XT", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Scorptec": "rx 7900 xt", "Umart": "rx 7900 xt", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 7900 XTX", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Mwave": "rx 7900 xtx", "MSY": "gpu_rx_7900xtx"}},
    {"part_key": "XFX Speedster RX 7900 XTX", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Umart": "xfx speedster rx 7900 xtx", "MSY": "gpu_all"}},
    {"part_key": "PowerColor Red Devil RX 7900 XTX", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Centre Com": "powercolor red devil rx 7900 xtx", "Umart": "powercolor red devil rx 7900 xtx", "MSY": "gpu_all"}},

    # --- RX 9000-series (with brand variants) ---
    {"part_key": "AMD Radeon RX 9060 XT", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Umart": "rx 9060 xt", "MSY": "gpu_rx_9060xt"}},
    {"part_key": "AMD Radeon RX 9070", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Centre Com": "rx 9070", "Umart": "rx 9070", "MSY": "gpu_all"}},
    {"part_key": "Gigabyte Gaming RX 9070", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Umart": "gigabyte gaming rx 9070", "MSY": "gpu_all"}},
    {"part_key": "AMD Radeon RX 9070 XT", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Scorptec": "rx 9070 xt", "MSY": "gpu_all"}},
    {"part_key": "Asus Prime RX 9070 XT", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Umart": "asus prime rx 9070 xt", "MSY": "gpu_all"}},
    {"part_key": "Sapphire Pulse RX 9070 XT", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Centre Com": "sapphire pulse rx 9070 xt", "Umart": "sapphire pulse rx 9070 xt", "MSY": "gpu_all"}},

    # ============================== RAM ==============================
    # --- DDR4 16GB (2x8GB) ---
    {"part_key": "Corsair Vengeance LPX 16GB (2x8GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "vengeance lpx 16gb ddr4 3200", "MSY": "ddr4_ram"}},
    {"part_key": "Kingston Fury Beast 16GB (2x8GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "fury beast 16gb ddr4 3200", "MSY": "ddr4_ram"}},
    {"part_key": "G.Skill Ripjaws V 16GB (2x8GB) DDR4 3600", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Centre Com": "ripjaws v 16gb ddr4 3600", "Umart": "ripjaws v 16gb ddr4 3600", "MSY": "ddr4_ram"}},

    # --- DDR4 32GB (2x16GB) ---
    {"part_key": "G.Skill Ripjaws V 32GB (2x16GB) DDR4 3600", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Centre Com": "ripjaws v 32gb ddr4 3600", "Scorptec": "ripjaws v 32gb ddr4 3600", "MSY": "ddr4_ram"}},
    {"part_key": "Corsair Vengeance LPX 32GB (2x16GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "vengeance lpx 32gb ddr4 3200", "MSY": "ddr4_ram"}},
    {"part_key": "Kingston Fury Beast 32GB (2x16GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "fury beast 32gb ddr4 3200", "MSY": "ddr4_ram"}},

    # --- DDR4 64GB (2x32GB) ---
    {"part_key": "Kingston Fury Beast 64GB (2x32GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "fury beast 64gb ddr4 3200", "MSY": "ddr4_ram"}},
    {"part_key": "Corsair Vengeance LPX 64GB (2x32GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "vengeance lpx 64gb ddr4 3200", "MSY": "ddr4_ram"}},
    {"part_key": "G.Skill Ripjaws V 64GB (2x32GB) DDR4 3600", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Centre Com": "ripjaws v 64gb ddr4 3600", "Umart": "ripjaws v 64gb ddr4 3600", "MSY": "ddr4_ram"}},

    # --- DDR5 16GB (2x8GB) ---
    {"part_key": "Corsair Vengeance 16GB (2x8GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "vengeance 16gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "Kingston Fury Beast 16GB (2x8GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "fury beast 16gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "G.Skill Trident Z5 16GB (2x8GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Centre Com": "trident z5 16gb ddr5 6000", "Umart": "trident z5 16gb ddr5 6000", "MSY": "ddr5_ram"}},

    # --- DDR5 32GB (2x16GB) ---
    {"part_key": "Corsair Vengeance 32GB (2x16GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "vengeance 32gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "Kingston Fury Beast 32GB (2x16GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "fury beast 32gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "G.Skill Trident Z5 32GB (2x16GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Centre Com": "trident z5 32gb ddr5 6000", "Scorptec": "trident z5 32gb ddr5 6000", "MSY": "ddr5_ram"}},

    # --- DDR5 64GB (2x32GB) ---
    {"part_key": "G.Skill Trident Z5 64GB (2x32GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Scorptec": "trident z5 64gb ddr5 6000", "Centre Com": "trident z5 64gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "Corsair Vengeance 64GB (2x32GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "vengeance 64gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "Kingston Fury Beast 64GB (2x32GB) DDR5 5600", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "fury beast 64gb ddr5 5600", "MSY": "ddr5_ram"}},

    # --- DDR5 96GB / 128GB (high-capacity) ---
    {"part_key": "G.Skill Trident Z5 96GB (2x48GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "trident z5 96gb ddr5 6000", "MSY": "ddr5_ram"}},
    {"part_key": "Kingston Fury Beast 128GB (2x64GB) DDR5 5600", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Mwave": "fury beast 128gb ddr5 5600", "Umart": "fury beast 128gb ddr5 5600", "MSY": "ddr5_ram"}},

    # ============================== SSD ==============================
    # Real listings use "500GB" as the label for this capacity tier, not
    # "512GB" — that's a marketing rounding that doesn't appear in actual
    # product titles.
    {"part_key": "Kingston NV3 500GB NVMe SSD", "category": "SSD", "subcategory": "500GB", "socket": None,
     "retailers": {"Umart": "kingston nv3 500gb", "MSY": "ssd"}},
    {"part_key": "Kingston NV3 1TB NVMe SSD", "category": "SSD", "subcategory": "1TB", "socket": None,
     "retailers": {"Umart": "kingston nv3 1tb", "MSY": "ssd"}},
    {"part_key": "Kingston NV3 2TB NVMe SSD", "category": "SSD", "subcategory": "2TB", "socket": None,
     "retailers": {"Umart": "kingston nv3 2tb", "MSY": "ssd"}},
    {"part_key": "Samsung 990 Pro 4TB PCIe 4.0 NVMe SSD", "category": "SSD", "subcategory": "4TB", "socket": None,
     "retailers": {"Centre Com": "samsung 990 pro 4tb", "Umart": "samsung 990 pro 4tb", "MSY": "ssd"}},

    # ========================== Motherboard ===========================
    {"part_key": "Gigabyte B550M K", "category": "Motherboard", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "b550m k", "MSY": "mobo_amd_am4"}},
    {"part_key": "ASRock B550M Pro4", "category": "Motherboard", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "b550m pro4", "MSY": "mobo_amd_am4"}},

    {"part_key": "MSI MAG B650 Tomahawk WiFi", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Centre Com": "mag b650 tomahawk", "Umart": "mag b650 tomahawk", "MSY": "mobo_amd_am5"}},
    {"part_key": "Asus TUF Gaming B650-Plus WiFi", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "tuf gaming b650-plus wifi", "MSY": "mobo_amd_am5"}},
    {"part_key": "MSI B850 Gaming Plus WiFi", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "b850 gaming plus wifi", "MSY": "mobo_amd_am5"}},
    {"part_key": "Asus Prime X870-P WiFi CSM", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Centre Com": "prime x870-p wifi", "Umart": "x870-p wifi", "MSY": "mobo_amd_am5"}},
    {"part_key": "MSI MAG X870 Tomahawk WiFi", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "mag x870 tomahawk wifi", "MSY": "mobo_amd_am5"}},

    {"part_key": "Asus Prime Z790-P WiFi CSM", "category": "Motherboard", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "prime z790-p wifi", "MSY": "mobo_intel_lga1700"}},
    {"part_key": "MSI PRO B760M-A WiFi", "category": "Motherboard", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "pro b760m-a wifi", "MSY": "mobo_intel_lga1700"}},

    {"part_key": "Gigabyte B860M Eagle WiFi6", "category": "Motherboard", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Centre Com": "b860m eagle wifi6", "Umart": "b860m eagle wifi6", "MSY": "mobo_intel_lga1851"}},
    {"part_key": "Asus TUF Gaming B860-Plus WiFi", "category": "Motherboard", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Umart": "tuf gaming b860-plus wifi", "MSY": "mobo_intel_lga1851"}},

    # ============================= Monitor ============================
    {"part_key": "Samsung 27in FHD IPS 120Hz Monitor", "category": "Monitor", "subcategory": "1080p", "socket": None,
     "retailers": {"Umart": "samsung 27in fhd ips 120hz", "MSY": "monitor_general"}},
    {"part_key": "MSI MAG 275QF-E20 WQHD Monitor", "category": "Monitor", "subcategory": "1440p", "socket": None,
     "retailers": {"Centre Com": "mag 275qf-e20", "Umart": "mag 275qf e20", "MSY": "monitor_general"}},
    {"part_key": "LG UltraFine 27UP600K-W 4K Monitor", "category": "Monitor", "subcategory": "4K", "socket": None,
     "retailers": {"Umart": "lg 27up600k", "MSY": "monitor_4k"}},
    {"part_key": "Asus ROG Swift PG27UCDM 4K QD-OLED Monitor", "category": "Monitor", "subcategory": "OLED", "socket": None,
     "retailers": {"Centre Com": "pg27ucdm", "Umart": "rog swift pg27ucdm", "MSY": "monitor_oled"}},
]
