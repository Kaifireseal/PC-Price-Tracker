"""
Low-level fetch + parse functions.

PARSING STRATEGY — heuristic, not hard-coded selectors
-------------------------------------------------------
Earlier versions of this scraper hard-coded CSS class names per retailer
(e.g. "product-item-link"). That's fragile in two ways: it requires
verified knowledge of each site's current markup (easy to get wrong), and
it breaks the moment a retailer redesigns their site.

Instead, this version finds products by *shape*, not by class name:
  - a plausible product link is an <a> tag with reasonably-long link text
    (a product title is rarely under ~15 characters or over ~150) that
    isn't an obvious nav/account/cart link
  - a plausible price is a "$1,234.56"-shaped string found in the nearest
    surrounding container (walking up a few parent levels from the link)

TWO FETCH ENGINES
------------------
  - fetch_with_requests(): plain HTTP GET. Only used for retailers confirmed
    to NOT block non-browser clients.
  - fetch_with_playwright(): a real headless Chromium instance, for sites
    that block plain HTTP clients at the connection level (Cloudflare-style
    bot management).
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
# Some sites style their nav bar as a <div> rather than a semantic <nav>
# tag (Umart/MSY both do this — a <div class="navigation"> wrapping their
# top promo bar). Tag-name checking alone missed this, letting a "Checkout
# Today's Hot Deals!" promo link through as if it were a product — which
# then caused a much bigger bug, see MAX_PRICE_CLIMB below.
NAV_CLASS_KEYWORDS = ("nav", "menu", "header", "footer", "promo", "banner", "hello")
# How many parent levels to climb looking for a price. Kept intentionally
# tight: when a stray link (nav, promo banner) isn't caught by the checks
# above, climbing too far risks reaching <body> and grabbing whatever the
# LARGEST price anywhere on the entire page happens to be — confirmed via
# debug_snippets.json to be exactly what was producing wildly wrong prices
# (e.g. $16,999 from an unrelated laptop, for a completely different
# product's search). A real product card's price is essentially always
# within 1-3 DOM levels of its title link; if nothing turns up in that
# range, treating it as "no price found" is far safer than falling back to
# an unrelated price further up the page.
MAX_PRICE_CLIMB = 3
CHALLENGE_MARKERS = (
    "checking your browser", "just a moment", "attention required",
    "cf-browser-verification", "cloudflare-challenge", "verify you are human",
)


def _is_nav_like(tag) -> bool:
    """True if this tag or its class list looks like a nav/menu/header/footer
    container, whether it's a semantic tag or just styled to look like one."""
    if tag.name in NAV_ANCESTOR_TAGS:
        return True
    classes = tag.get("class") or []
    class_str = " ".join(classes).lower()
    return any(keyword in class_str for keyword in NAV_CLASS_KEYWORDS)


DEBUG_SNIPPETS = {}


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


def _clean_price(raw_text: str):
    match = PRICE_RE.search(raw_text.replace("\xa0", " "))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _absolute_url(base_domain: str, href: str) -> str:
    if href.startswith("http"):
        return href
    return urljoin(base_domain, href)


def _looks_like_bot_challenge(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in CHALLENGE_MARKERS)


def _parse_html(html: str, base_domain: str, retailer_name: str = None):
    """Generic, selector-free product extraction. See module docstring."""
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
        for _ in range(MAX_PRICE_CLIMB):
            node = node.parent
            if node is None:
                break
            matches = PRICE_RE.findall(node.get_text(" ", strip=True))
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
                break

        if price is None:
            continue

        if price_context_key and price_context_key not in DEBUG_SNIPPETS and matched_node is not None:
            DEBUG_SNIPPETS[price_context_key] = {
                "note": f"Ancestor HTML used to find the price for the first product on this page: '{title}' -> matched price ${price}",
                "raw_ancestor_html": str(matched_node)[:4000],
            }

        seen_urls.add(url)
        results.append({"title": title, "price": price, "url": url})

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
