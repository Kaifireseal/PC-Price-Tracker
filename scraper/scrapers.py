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
# centered on the first real price-shaped match on the page. This gets
# written out to debug_snippets.json at the end of a run so real markup can
# be inspected without any manual steps.
DEBUG_SNIPPETS = {}


def _record_snippet(retailer_name: str, html: str):
    if retailer_name in DEBUG_SNIPPETS:
        return  # already captured one for this retailer this run
    # Use the same PRICE_RE as real parsing (a "$" followed by digits) so we
    # don't center on false positives like a CSS icon-font glyph definition
    # such as --fa:"\$" — those contain a dollar sign but no digits.
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
        "snippet": html
