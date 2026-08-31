"""
Low-level fetch + parse functions.

PARSING STRATEGY — heuristic, not hard-coded selectors
-------------------------------------------------------
Finds products by *shape*, not by class name:
  - a plausible product link is an <a> tag with reasonably-long link text
  - a plausible price is a "$1,234.56"-shaped string found in a nearby
    parent container (tight radius — see MAX_PRICE_CLIMB)
  - stock status is looked for in that same nearby container, using common
    phrases AU retailers use ("In Stock", "Out of Stock", "X available",
    etc.) — best-effort: if nothing recognizable is found, status comes
    back as "unknown" rather than guessing.
  - a product image is looked for in that SAME nearby container (the
    ancestor node where the price was found is almost always the whole
    product card, which also holds the thumbnail) — best-effort, comes
    back as None if nothing usable is found.

TWO FETCH ENGINES
------------------
  - fetch_with_requests(): plain HTTP GET, for retailers confirmed to not
    block non-browser clients.
  - fetch_with_playwright(): real headless Chromium, for retailers that do.
"""

import re
import time
import random
import logging
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from config import COMMON_HEADERS, RETAILERS

logger = logging.getLogger("scraper")

PRICE_RE = re.compile(r"\$\s?([\d,]+(?:\.\d{2})?)")
MIN_TITLE_LEN = 15
MAX_TITLE_LEN = 150
SKIP_HREF_PATTERNS = (
    "#", "javascript:", "mailto:", "tel:",
    "/cart", "/account", "/login", "/wishlist", "/compare",
    "/checkout", "/customer", "/register",
)
NAV_ANCESTOR_TAGS = ("nav", "header", "footer", "aside")
NAV_CLASS_KEYWORDS = ("nav", "menu", "header", "footer", "promo", "banner", "hello")
MAX_PRICE_CLIMB = 4
CHALLENGE_MARKERS = (
    "checking your browser", "just a moment", "attention required",
    "cf-browser-verification", "cloudflare-challenge", "verify you are human",
)

# Keywords that suggest an <img> is a logo/icon/badge rather than an actual
# product photo — skipped when picking which image to use.
IMAGE_SKIP_KEYWORDS = (
    "logo", "icon", "badge", "sprite", "placeholder", "spinner", "loading",
    "payment", "visa", "mastercard", "paypal", "afterpay", "zip",
)

# Stock-status detection, checked in the same nearby container the price
# was found in. The quantity regex uses a negative lookbehind so it can't
# accidentally grab the trailing zeros off a price (e.g. "$549.00 In Stock"
# was originally misread as "0 in stock" — the ".00" right before "In
# Stock" looked like a quantity). "0 in stock" is intentionally NOT in the
# phrase list below for the same reason — it's a substring of any price
# ending "X0.00 In Stock", so it was firing constantly on ordinary in-stock
# listings. Genuine zero-quantity is instead caught correctly by the regex.
STOCK_QTY_RE = re.compile(
    r"(?<![\d.])(?:only\s+)?(\d+)\s*(?:in\s*stock|left|available|units?\s*(?:left|available))",
    re.IGNORECASE,
)
OUT_OF_STOCK_PHRASES = (
    "out of stock", "sold out", "unavailable", "notify me", "email when available",
    "currently unavailable",
)
IN_STOCK_PHRASES = (
    "in stock", "available now", "add to cart", "add to basket", "ships today",
    "ready to ship", "instock",
)
PREORDER_PHRASES = ("pre-order", "preorder", "coming soon", "backorder")


def _is_nav_like(tag) -> bool:
    if tag.name in NAV_ANCESTOR_TAGS:
        return True
    classes = tag.get("class") or []
    class_str = " ".join(classes).lower()
    return any(keyword in class_str for keyword in NAV_CLASS_KEYWORDS)


def _detect_stock(text: str):
    """
    Returns (status, qty). status is one of:
      "in_stock", "out_of_stock", "preorder", "unknown"
    qty is an int if a specific number was found, else None.
    """
    lowered = text.lower()

    qty_match = STOCK_QTY_RE.search(lowered)
    if qty_match:
        qty = int(qty_match.group(1))
        return ("out_of_stock" if qty == 0 else "in_stock"), qty

    if any(phrase in lowered for phrase in OUT_OF_STOCK_PHRASES):
        return "out_of_stock", None
    if any(phrase in lowered for phrase in PREORDER_PHRASES):
        return "preorder", None
    if any(phrase in lowered for phrase in IN_STOCK_PHRASES):
        return "in_stock", None

    return "unknown", None


def _extract_image_url(node, base_domain: str):
    """
    Best-effort product image lookup within the same ancestor container
    the price was matched in. Handles common lazy-load patterns (data-src,
    data-original, srcset) since plain <img src="..."> is often a tiny
    placeholder until JS swaps it in — which we never run in requests mode.
    Returns None if nothing usable is found, rather than guessing.
    """
    if node is None:
        return None

    for img in node.find_all("img"):
        candidate = (
            img.get("data-src")
            or img.get("data-original")
            or img.get("data-lazy-src")
            or img.get("src")
        )
        if not candidate:
            srcset = img.get("srcset") or img.get("data-srcset")
            if srcset:
                candidate = srcset.split(",")[0].strip().split(" ")[0]

        if not candidate or candidate.startswith("data:"):
            continue

        lowered = candidate.lower()
        if any(kw in lowered for kw in IMAGE_SKIP_KEYWORDS):
            continue

        return _absolute_url(base_domain, candidate)

    return None


DEBUG_SNIPPETS = {}
TARGET_DEBUG_KEYWORDS = ()  # populate temporarily when chasing a specific product's bug


def _record_snippet(retailer_name: str, html: str):
    if retailer_name in DEBUG_SNIPPETS:
        return
    match = PRICE_RE.search(html)
    if not match:
        DEBUG_SNIPPETS[retailer_name] = {
            "note": "No '$<digits>'-shaped price found anywhere on the page.",
            "html_length": len(html),
            "snippet": html[:2000],
        }
        return
    start = max(0, match.start() - 1500)
    end = min(len(html), match.start() + 1500)
    DEBUG_SNIPPETS[retailer_name] = {
        "note": "Snippet centered on the first '$<digits>'-shaped price found on the page.",
        "html_length": len(html),
        "snippet": html[start:end],
    }


def _absolute_url(base_domain: str, href: str) -> str:
    if href.startswith("http"):
        return href
    return urljoin(base_domain, href)


def _looks_like_bot_challenge(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in CHALLENGE_MARKERS)


def _parse_html(html: str, base_domain: str, retailer_name: str = None):
    if _looks_like_bot_challenge(html):
        raise RuntimeError("BOT_CHALLENGE: page returned a bot-verification challenge instead of results")

    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen_urls = set()
    price_context_key = f"{retailer_name}_price_context" if retailer_name else None

    for a in soup.find_all("a", href=True):
        if any(_is_nav_like(parent) for parent in a.find_parents()):
            continue

        title = a.get_text(strip=True)
        if not (MIN_TITLE_LEN <= len(title) <= MAX_TITLE_LEN):
            continue

        href = a["href"]
        if any(p in href.lower() for p in SKIP_HREF_PATTERNS):
            continue

        url = _absolute_url(base_domain, href)
        if url in seen_urls:
            continue

        price = None
        node = a
        matched_node = None
        matched_text = ""
        for _ in range(MAX_PRICE_CLIMB):
            node = node.parent
            if node is None:
                break
            node_text = node.get_text(" ", strip=True)
            clean_text = re.sub(
                r"(?:you\s+)?save\s*:?\s*\$\s?[\d,]+(?:\.\d{2})?", "", node_text, flags=re.IGNORECASE
            )
            matches = PRICE_RE.findall(clean_text)
            if matches:
                candidates = []
                for m in matches:
                    try:
                        candidates.append(float(m.replace(",", "")))
                    except ValueError:
                        pass
                if candidates:
                    price = max(candidates)
                    matched_node = node
                    matched_text = node_text
                    break

        if price is None:
            continue

        stock_status, stock_qty = _detect_stock(matched_text)
        image_url = _extract_image_url(matched_node, base_domain)

        if price_context_key and price_context_key not in DEBUG_SNIPPETS and matched_node is not None:
            DEBUG_SNIPPETS[price_context_key] = {
                "note": f"Ancestor HTML used to find the price for the first product on this page: '{title}' -> matched price ${price}, stock={stock_status}, image={image_url}",
                "raw_ancestor_html": str(matched_node)[:4000],
            }

        if retailer_name and matched_node is not None:
            for keyword in TARGET_DEBUG_KEYWORDS:
                if keyword.lower() in title.lower():
                    target_key = f"{retailer_name}_TARGET_{keyword}"
                    if target_key not in DEBUG_SNIPPETS:
                        DEBUG_SNIPPETS[target_key] = {
                            "note": f"Ancestor HTML for '{title}' -> price ${price}, stock={stock_status}, image={image_url}",
                            "raw_ancestor_html": str(matched_node)[:4000],
                        }

        seen_urls.add(url)
        results.append({
            "title": title, "price": price, "url": url,
            "stock_status": stock_status, "stock_qty": stock_qty,
            "image_url": image_url,
        })

        if len(results) >= 100:
            break

    return results


def _build_url(rule: dict, query: str) -> str:
    if rule.get("url_mode") == "category":
        from config import CATEGORY_URLS
        return CATEGORY_URLS[query]
    return rule["search_url"].format(query=quote_plus(query))


def fetch_with_requests(retailer_name: str, query: str, max_retries: int = 3):
    rule = RETAILERS[retailer_name]
    url = _build_url(rule, query)
    base_domain = re.match(r"https?://[^/]+", url).group(0)

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=COMMON_HEADERS, timeout=15)
            if resp.status_code in (403, 429):
                raise RuntimeError(f"HTTP {resp.status_code} (likely bot-blocked)")
            resp.raise_for_status()
            _record_snippet(retailer_name, resp.text)
            return _parse_html(resp.text, base_domain, retailer_name)
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Attempt %s/%s failed for %s (%s): %s",
                attempt, max_retries, retailer_name, query, exc,
            )
            time.sleep(1.5 * attempt + random.uniform(0, 1))
    raise RuntimeError(f"{retailer_name} failed after {max_retries} attempts: {last_exc}")


def fetch_with_playwright(retailer_name: str, query: str, max_retries: int = 2):
    from playwright.sync_api import sync_playwright

    rule = RETAILERS[retailer_name]
    url = _build_url(rule, query)
    base_domain = re.match(r"https?://[^/]+", url).group(0)

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent=COMMON_HEADERS["User-Agent"],
                    locale="en-AU",
                    viewport={"width": 1366, "height": 900},
                    extra_http_headers={"Accept-Language": "en-AU,en;q=0.9"},
                )
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                page = context.new_page()
                page.goto(url, timeout=25000, wait_until="domcontentloaded")

                for _ in range(5):
                    current_html = page.content()
                    if not _looks_like_bot_challenge(current_html):
                        break
                    page.wait_for_timeout(2000)
                html = page.content()
                browser.close()

            _record_snippet(retailer_name, html)
            return _parse_html(html, base_domain, retailer_name)

        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Playwright attempt %s/%s failed for %s (%s): %s",
                attempt, max_retries, retailer_name, query, exc,
            )
            time.sleep(2 * attempt)
    raise RuntimeError(f"{retailer_name} (playwright) failed after {max_retries} attempts: {last_exc}")


def fetch_search_results(retailer_name: str, query: str):
    rule = RETAILERS[retailer_name]
    if rule["mode"] == "playwright":
        return fetch_with_playwright(retailer_name, query)
    return fetch_with_requests(retailer_name, query)
