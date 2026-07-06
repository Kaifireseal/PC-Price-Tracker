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

This is less surgically precise than a verified selector, but it doesn't
depend on guessing implementation details we can't see, and it keeps working
across most storefront redesigns since the *shape* of "title link next to a
price" is far more stable than any specific class name.

TWO FETCH ENGINES
------------------
  - fetch_with_requests(): plain HTTP GET. Only used for retailers confirmed
    to NOT block non-browser clients (see config.py comments for how that
    was determined).
  - fetch_with_playwright(): a real headless Chromium instance, for sites
    that block plain HTTP clients at the connection level (Cloudflare-style
    bot management). This presents a genuine browser fingerprint, which
    such systems check for — but it is NOT a guaranteed bypass. Some
    Cloudflare configurations (interactive "Turnstile" challenges) can still
    detect and block headless automation. When that happens, this function
    detects the tell-tale challenge page and raises a clear, distinct error
    (BOT_CHALLENGE) so it's never confused with a broken parser.
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
CHALLENGE_MARKERS = (
    "checking your browser", "just a moment", "attention required",
    "cf-browser-verification", "cloudflare-challenge", "verify you are human",
)

# Captures ONE raw-HTML snippet per retailer (the first time we see it),
# centered on the first "$" found on the page. This gets written out to
# debug_snippets.json at the end of a run so real markup can be inspected
# without any manual steps — same idea as the Apps Script "Debug" sheet.
DEBUG_SNIPPETS = {}


def _record_snippet(retailer_name: str, html: str):
    if retailer_name in DEBUG_SNIPPETS:
        return  # already captured one for this retailer this run
    dollar_index = html.find("$")
    if dollar_index == -1:
        DEBUG_SNIPPETS[retailer_name] = {
            "note": "No '$' found anywhere on the page.",
            "html_length": len(html),
            "snippet": html[:2000],
        }
        return
    start = max(0, dollar_index - 1500)
    end = min(len(html), dollar_index + 1500)
    DEBUG_SNIPPETS[retailer_name] = {
        "note": "Snippet centered on the first '$' found on the page.",
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


def _parse_html(html: str, base_domain: str):
    """Generic, selector-free product extraction. See module docstring."""
    if _looks_like_bot_challenge(html):
        raise RuntimeError("BOT_CHALLENGE: page returned a bot-verification challenge instead of results")

    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        if not (MIN_TITLE_LEN <= len(title) <= MAX_TITLE_LEN):
            continue

        href = a["href"]
        if any(p in href.lower() for p in SKIP_HREF_PATTERNS):
            continue

        url = _absolute_url(base_domain, href)
        if url in seen_urls:
            continue

        # Walk up a few parent containers looking for a nearby price. Most
        # storefronts render title + price inside the same "product card"
        # container, usually within 2-4 DOM levels of the link.
        price = None
        node = a
        for _ in range(5):
            node = node.parent
            if node is None:
                break
            match = PRICE_RE.search(node.get_text(" ", strip=True))
            if match:
                price = _clean_price(match.group(0))
                break

        if price is None:
            continue

        seen_urls.add(url)
        results.append({"title": title, "price": price, "url": url})

        if len(results) >= 15:  # plenty of candidates for matcher.py to rank
            break

    return results


def fetch_with_requests(retailer_name: str, query: str, max_retries: int = 3):
    rule = RETAILERS[retailer_name]
    url = rule["search_url"].format(query=quote_plus(query))
    base_domain = re.match(r"https?://[^/]+", url).group(0)

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=COMMON_HEADERS, timeout=15)
            if resp.status_code in (403, 429):
                raise RuntimeError(f"HTTP {resp.status_code} (likely bot-blocked)")
            resp.raise_for_status()
            _record_snippet(retailer_name, resp.text)
            return _parse_html(resp.text, base_domain)
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Attempt %s/%s failed for %s (%s): %s",
                attempt, max_retries, retailer_name, query, exc,
            )
            time.sleep(1.5 * attempt + random.uniform(0, 1))
    raise RuntimeError(f"{retailer_name} failed after {max_retries} attempts: {last_exc}")


def fetch_with_playwright(retailer_name: str, query: str, max_retries: int = 2):
    """
    Uses a real headless browser for sites that block plain HTTP clients.
    Requires: pip install playwright && playwright install chromium
    """
    from playwright.sync_api import sync_playwright

    rule = RETAILERS[retailer_name]
    url = rule["search_url"].format(query=quote_plus(query))
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
                # Basic stealth: hide the most obvious "this is automation"
                # signal. This clears naive checks but will NOT defeat
                # Cloudflare's more advanced fingerprinting on its own.
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                page = context.new_page()
                page.goto(url, timeout=25000, wait_until="domcontentloaded")
                # Give any Cloudflare "checking your browser" interstitial a
                # moment to resolve and redirect to the real page.
                page.wait_for_timeout(3500)
                html = page.content()
                browser.close()

            _record_snippet(retailer_name, html)
            return _parse_html(html, base_domain)

        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Playwright attempt %s/%s failed for %s (%s): %s",
                attempt, max_retries, retailer_name, query, exc,
            )
            time.sleep(2 * attempt)
    raise RuntimeError(f"{retailer_name} (playwright) failed after {max_retries} attempts: {last_exc}")


def fetch_search_results(retailer_name: str, query: str):
    """Dispatches to the right engine based on config.py's 'mode' field."""
    rule = RETAILERS[retailer_name]
    if rule["mode"] == "playwright":
        return fetch_with_playwright(retailer_name, query)
    return fetch_with_requests(retailer_name, query)
