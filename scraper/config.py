"""
Central configuration for the AU PC Part Price Tracker.

RETAILERS — one entry per store: how to build a URL, and which fetch
engine to use.

  mode: "requests"   -> fast, plain HTTP GET (BeautifulSoup parses result).
  mode: "playwright"  -> real headless Chromium, for sites that block plain
                        HTTP clients at the connection level.

  url_mode: "search"  -> "search_url" is a template with {query}.
  url_mode: "category" -> "search_url" is used AS-IS. Used for MSY and PLE
                        Computers, neither of which has a simple search
                        endpoint that returns results without JavaScript —
                        instead we point straight at stable category
                        listing pages. The "query" value in TRACKED_PARTS
                        is then a label into CATEGORY_URLS below.

CONFIRMED STATUS (from actual diagnostic runs):
  - Centre Com, Scorptec, Mwave: REMOVED. Confirmed permanently blocked
    (Cloudflare Turnstile / AWS WAF) even through Playwright.
  - JW Computers: REMOVED. Tested in isolation on 4 parts - the debug
    snippet showed a Cloudflare "Just a moment..." Turnstile challenge
    page, the same wall that blocks Centre Com/Scorptec. Confirmed dead
    end, do not re-add without a fundamentally different approach.
  - BPC Tech: TESTING IN ISOLATION on the same 4 parts (AMD Ryzen 5 7600,
    AMD Ryzen 7 9800X3D, Intel Core i5-14400F, NVIDIA RTX 5070). A direct
    plain-HTTP fetch was blocked by bot detection earlier, so this is a
    weaker candidate than JW Computers was - if this also comes back
    Cloudflare-challenged in the debug snippets, both experimental
    retailers are dead ends and the tracker should stay on Umart / MSY /
    PLE Computers only.
  - Umart, MSY: confirmed working reliably via plain "requests".
  - PLE Computers: search page (/Search/{query}) is JS-rendered and comes
    back empty via plain requests — but category browse pages are fully
    server-rendered with real prices, so it uses url_mode "category" like
    MSY rather than a search query.

SUBCATEGORY: every part carries a "subcategory" alongside "category" —
socket for CPUs/motherboards (AM4/AM5/LGA1700/LGA1851), generation for GPUs
(RTX 30/40/50-series, RX 7000/9000-series), DDR generation for RAM,
capacity for SSDs, and display type for monitors. This drives the
dashboard's second-level filter pills.

TRACKED_PARTS — the shopping list: canonical part name, category,
subcategory, and the search query (or category label) to use per
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
    "PLE Computers": {
        "mode": "requests",
        "url_mode": "category",
        "search_url": None,
    },
    "BPC Tech": {
        "mode": "playwright",
        "url_mode": "search",
        "search_url": "https://www.bpctech.com.au/catalogsearch/result/?q={query}",
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
    "ple_amd_cpu": "https://www.ple.com.au/Categories/235/CPUs/Brands/149/AMD",
    "ple_intel_cpu": "https://www.ple.com.au/Categories/235/CPUs/Brands/121/Intel",
    "ple_gpu_all": "https://www.ple.com.au/categories/259/graphics-cards",
    "ple_ram": "https://www.ple.com.au/Categories/282/Memory-RAM",
    "ple_motherboards": "https://www.ple.com.au/Categories/302/Motherboards",
    "ple_monitors": "https://www.ple.com.au/Categories/296/Monitors",
    "ple_ssd": "https://www.ple.com.au/Categories/243/Hard-Drives-and-SSDs",
}

TRACKED_PARTS = [
    {"part_key": "AMD Ryzen 5 5500GT", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "ryzen 5 5500gt", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 5600GT", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "ryzen 5 5600gt", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 5500", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "ryzen 5 5500", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 5600", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "ryzen 5 5600", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 5600X", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "ryzen 5 5600x", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 7 5700X", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "5700x", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 7 5800X3D", "category": "CPU", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "5800x3d", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 7500F", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 7500f", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 7500X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 7500x3d", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 7600", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu", "BPC Tech": "amd ryzen 5 7600"}},
    {"part_key": "AMD Ryzen 5 7600X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 9600", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 9600", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 9600X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 9600x", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 5 9500F", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 5 9500f", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 7 7700X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 7 7700x", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 7 7800X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "7800x3d", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 7 9800X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "9800x3d", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu", "BPC Tech": "9800x3d"}},
    {"part_key": "AMD Ryzen 9 7900X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 9 7900x", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 9 7950X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 9 7950x", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9900X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "9900x3d", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9950X", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "ryzen 9 9950x", "MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9950X3D", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "AMD Ryzen 9 9950X3D2", "category": "CPU", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"MSY": "amd_cpu", "PLE Computers": "ple_amd_cpu"}},
    {"part_key": "Intel Core i5-13400F", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "i5-13400f", "MSY": "intel_cpu", "PLE Computers": "ple_intel_cpu"}},
    {"part_key": "Intel Core i5-14400F", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "i5-14400f", "MSY": "intel_cpu", "PLE Computers": "ple_intel_cpu", "BPC Tech": "i5-14400f"}},
    {"part_key": "Intel Core i5-12400F", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"MSY": "intel_cpu", "PLE Computers": "ple_intel_cpu"}},
    {"part_key": "Intel Core i7-14700K", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "14700k", "MSY": "intel_cpu", "PLE Computers": "ple_intel_cpu"}},
    {"part_key": "Intel Core i9-14900K", "category": "CPU", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "14900k", "MSY": "intel_cpu", "PLE Computers": "ple_intel_cpu"}},
    {"part_key": "Intel Core Ultra 5 245K", "category": "CPU", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Umart": "ultra 5 245k", "MSY": "intel_cpu", "PLE Computers": "ple_intel_cpu"}},
    {"part_key": "Intel Core Ultra 7 265K", "category": "CPU", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"MSY": "intel_cpu", "PLE Computers": "ple_intel_cpu"}},
    {"part_key": "Intel Core Ultra 9 285K", "category": "CPU", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Umart": "ultra 9 285k", "MSY": "intel_cpu", "PLE Computers": "ple_intel_cpu"}},
    {"part_key": "NVIDIA RTX 3060", "category": "GPU", "subcategory": "RTX 30-series", "socket": None,
     "retailers": {"Umart": "rtx 3060", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 4060", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Umart": "rtx 4060", "MSY": "gpu_rtx_4060", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 4060 Ti", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Umart": "rtx 4060 ti", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 4070", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Umart": "rtx 4070", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 4070 Ti Super", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Umart": "rtx 4070 ti super", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 4090", "category": "GPU", "subcategory": "RTX 40-series", "socket": None,
     "retailers": {"Umart": "rtx 4090", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 5060", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Umart": "rtx 5060", "MSY": "gpu_rtx_5060", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 5060 Ti", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Umart": "rtx 5060 ti", "MSY": "gpu_rtx_5060ti", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 5070", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"MSY": "gpu_rtx_5070", "PLE Computers": "ple_gpu_all", "BPC Tech": "nvidia rtx 5070"}},
    {"part_key": "NVIDIA RTX 5070 Ti", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Umart": "rtx 5070 ti", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 5080", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Umart": "rtx 5080", "MSY": "gpu_rtx_5080", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "NVIDIA RTX 5090", "category": "GPU", "subcategory": "RTX 50-series", "socket": None,
     "retailers": {"Umart": "rtx 5090", "MSY": "gpu_rtx_5090", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "AMD Radeon RX 7600", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Umart": "rx 7600", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "AMD Radeon RX 7900 XTX", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"MSY": "gpu_rx_7900xtx", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "XFX Speedster RX 7900 XTX", "category": "GPU", "subcategory": "RX 7000-series", "socket": None,
     "retailers": {"Umart": "xfx speedster rx 7900 xtx", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "AMD Radeon RX 9060 XT", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Umart": "rx 9060 xt", "MSY": "gpu_rx_9060xt", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "AMD Radeon RX 9070", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Umart": "rx 9070", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "Gigabyte Gaming RX 9070", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Umart": "gigabyte gaming rx 9070", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "AMD Radeon RX 9070 XT", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "Gigabyte Radeon RX 9070 GRE", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "Asus Prime RX 9070 XT", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Umart": "asus prime rx 9070 xt", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "Sapphire Pulse RX 9070 XT", "category": "GPU", "subcategory": "RX 9000-series", "socket": None,
     "retailers": {"Umart": "sapphire pulse rx 9070 xt", "MSY": "gpu_all", "PLE Computers": "ple_gpu_all"}},
    {"part_key": "Corsair Vengence 16GB (2x8GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "corsair lpx 16gb ddr4 3200", "MSY": "ddr4_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Kingston Fury Beast 16GB (2x8GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "fury beast 16gb ddr4 3200", "MSY": "ddr4_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "G.Skill Ripjaws V 16GB (2x8GB) DDR4 3600", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "ripjaws v 16gb ddr4 3600", "MSY": "ddr4_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Adata 16GB (2x8GB) DDR4 3200 XPG", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "adata 16gb ddr4 3200 xpg", "MSY": "ddr4_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "G.Skill Ripjaws V 32GB (2x16GB) DDR4 3600", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"MSY": "ddr4_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Corsair Vengeance LPX 32GB (2x16GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "vengeance lpx 32gb ddr4 3200", "MSY": "ddr4_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Kingston Fury Beast 32GB (2x16GB) DDR4 3200", "category": "RAM", "subcategory": "DDR4", "socket": None,
     "retailers": {"Umart": "fury beast 32gb ddr4 3200", "MSY": "ddr4_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Corsair Vengence 16GB (2x8GB) DDR5 5200", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "corsair 16gb ddr5 5200", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Kingston 16GB (2x8GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "kingston 16gb ddr5 6000", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "G.Skill Trident Z5 16GB (2x8GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "trident z5 16gb ddr5 6000", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Corsair Vengeance 32GB (2x16GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "vengeance 32gb ddr5 6000", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Kingston Fury Beast 32GB (2x16GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "fury beast 32gb ddr5 6000", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Silicon Power XPOWER Zenith 32GB (2x16GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "G.Skill Trident Z5 64GB (2x32GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Corsair Vengeance 64GB (2x32GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "vengeance 64gb ddr5 6000", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Kingston Fury Beast 64GB (2x32GB) DDR5 5600", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "kingston 64gb ddr5 5600", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "TeamGroup Delta 96GB (2x48GB) DDR5 6800", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "teamgroup delta 96gb ddr5 6800", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Corsair Vengence 96GB (2x48GB) DDR5 6000", "category": "RAM", "subcategory": "DDR5", "socket": None,
     "retailers": {"Umart": "fury beast 128gb ddr5 5600", "MSY": "ddr5_ram", "PLE Computers": "ple_ram"}},
    {"part_key": "Kingston NV3 500GB NVMe SSD", "category": "SSD", "subcategory": "500GB", "socket": None,
     "retailers": {"Umart": "kingston nv3 500gb", "MSY": "ssd", "PLE Computers": "ple_ssd"}},
    {"part_key": "SP Silicon Power UD90 500GB NVMe SSD", "category": "SSD", "subcategory": "500GB", "socket": None,
     "retailers": {"Umart": "sp silicon power ud90 500gb", "MSY": "ssd", "PLE Computers": "ple_ssd"}},
    {"part_key": "Kingston NV3 1TB NVMe SSD", "category": "SSD", "subcategory": "1TB", "socket": None,
     "retailers": {"Umart": "kingston nv3 1tb", "MSY": "ssd", "PLE Computers": "ple_ssd"}},
    {"part_key": "Samsung 990 Pro 1TB NVMe SSD", "category": "SSD", "subcategory": "1TB", "socket": None,
     "retailers": {"Umart": "samsung 990 pro 1tb", "MSY": "ssd", "PLE Computers": "ple_ssd"}},
    {"part_key": "Kingston NV3 2TB NVMe SSD", "category": "SSD", "subcategory": "2TB", "socket": None,
     "retailers": {"Umart": "kingston nv3 2tb", "MSY": "ssd", "PLE Computers": "ple_ssd"}},
    {"part_key": "Crucial P310 2TB NVMe SSD", "category": "SSD", "subcategory": "2TB", "socket": None,
     "retailers": {"Umart": "crucial p310 2tb", "MSY": "ssd", "PLE Computers": "ple_ssd"}},
    {"part_key": "Samsung 990 Pro 4TB PCIe 4.0 NVMe SSD", "category": "SSD", "subcategory": "4TB", "socket": None,
     "retailers": {"Umart": "samsung 990 pro 4tb", "MSY": "ssd", "PLE Computers": "ple_ssd"}},
    {"part_key": "Crucial 4TB PCIe 4.0 NVMe SSD", "category": "SSD", "subcategory": "4TB", "socket": None,
     "retailers": {"Umart": "crucial 4tb", "MSY": "ssd", "PLE Computers": "ple_ssd"}},
    {"part_key": "Gigabyte B550M K", "category": "Motherboard", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "b550m k", "MSY": "mobo_amd_am4", "PLE Computers": "ple_motherboards"}},
    {"part_key": "ASRock B550M Pro4", "category": "Motherboard", "subcategory": "AM4", "socket": "AM4",
     "retailers": {"Umart": "b550m pro4", "MSY": "mobo_amd_am4", "PLE Computers": "ple_motherboards"}},
    {"part_key": "MSI MAG B650 Tomahawk WiFi", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "mag b650 tomahawk", "MSY": "mobo_amd_am5", "PLE Computers": "ple_motherboards"}},
    {"part_key": "Asus TUF Gaming B650-Plus WiFi", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "tuf gaming b650-plus wifi", "MSY": "mobo_amd_am5", "PLE Computers": "ple_motherboards"}},
    {"part_key": "MSI B850 Gaming Plus WiFi", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "b850 gaming plus wifi", "MSY": "mobo_amd_am5", "PLE Computers": "ple_motherboards"}},
    {"part_key": "Asus Prime X870-P WiFi CSM", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "x870-p wifi", "MSY": "mobo_amd_am5", "PLE Computers": "ple_motherboards"}},
    {"part_key": "MSI MAG X870 Tomahawk WiFi", "category": "Motherboard", "subcategory": "AM5", "socket": "AM5",
     "retailers": {"Umart": "mag x870 tomahawk wifi", "MSY": "mobo_amd_am5", "PLE Computers": "ple_motherboards"}},
    {"part_key": "Asus Prime Z790-P WiFi CSM", "category": "Motherboard", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "prime z790-p wifi", "MSY": "mobo_intel_lga1700", "PLE Computers": "ple_motherboards"}},
    {"part_key": "MSI PRO B760M-A WiFi", "category": "Motherboard", "subcategory": "LGA1700", "socket": "LGA1700",
     "retailers": {"Umart": "pro b760m-a wifi", "MSY": "mobo_intel_lga1700", "PLE Computers": "ple_motherboards"}},
    {"part_key": "Gigabyte B860M Eagle WiFi6", "category": "Motherboard", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Umart": "b860m eagle wifi6", "MSY": "mobo_intel_lga1851", "PLE Computers": "ple_motherboards"}},
    {"part_key": "Asus TUF Gaming B860-Plus WiFi", "category": "Motherboard", "subcategory": "LGA1851", "socket": "LGA1851",
     "retailers": {"Umart": "tuf gaming b860-plus wifi", "MSY": "mobo_intel_lga1851", "PLE Computers": "ple_motherboards"}},
    {"part_key": "Samsung 27in FHD IPS 120Hz Monitor", "category": "Monitor", "subcategory": "1080p", "socket": None,
     "retailers": {"Umart": "samsung 27in fhd ips 120hz", "MSY": "monitor_general", "PLE Computers": "ple_monitors"}},
    {"part_key": "MSI MAG 275QF-E20 WQHD Monitor", "category": "Monitor", "subcategory": "1440p", "socket": None,
     "retailers": {"Umart": "mag 275qf e20", "MSY": "monitor_general", "PLE Computers": "ple_monitors"}},
    {"part_key": "LG UltraFine 27UP600K-W 4K Monitor", "category": "Monitor", "subcategory": "4K", "socket": None,
     "retailers": {"Umart": "lg 27up600k", "MSY": "monitor_4k", "PLE Computers": "ple_monitors"}},
    {"part_key": "Asus ROG Swift PG27UCDM 4K QD-OLED Monitor", "category": "Monitor", "subcategory": "OLED", "socket": None,
     "retailers": {"Umart": "rog swift pg27ucdm", "MSY": "monitor_oled", "PLE Computers": "ple_monitors"}},
]
