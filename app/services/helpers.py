import re
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup, Tag
from typing import Optional, Dict
import json

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; InsightsFetcher/1.0; +https://example.com/bot)",
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
}

def norm_base(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or parsed.path
    return f"{scheme}://{netloc}".rstrip("/")

async def fetch_text(client: httpx.AsyncClient, url: str) -> str:
    r = await client.get(url, headers=DEFAULT_HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

async def fetch_json(client: httpx.AsyncClient, url: str):
    r = await client.get(url, headers=DEFAULT_HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")

def is_shopify_html(html: str) -> bool:
    # Multiple signals—don’t rely on one
    needles = [
        "cdn.shopify.com", "myshopify.com", "Shopify.theme", "ShopifyAnalytics",
        'content="Shopify"', "shopify_pay", "shopify-section"
    ]
    return any(n.lower() in html.lower() for n in needles)

def absolute(base: str, href: str | None) -> str | None:
    if not href: return None
    return urljoin(base + "/", href)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,4}\)?[\s-]?)\d{3,4}[\s-]?\d{3,4})")


# --- NEW HELPER: For cleaning price strings ---
def clean_price_string(price_text: str) -> str:
    """Removes currency symbols and non-numeric characters to get a clean price."""
    if not price_text:
        return ""
    # This regex will remove anything that isn't a digit or a decimal point
    cleaned = re.sub(r'[^\d\.]', '', price_text)
    return cleaned

# --- NEW HELPER: For getting data from JSON-LD scripts ---
def get_data_from_json_ld(soup: BeautifulSoup | Tag) -> Optional[Dict]:
    """Finds and parses the JSON-LD script tag in a soup object."""
    try:
        script = soup.find("script", type="application/ld+json")
        if script and script.string:
            return json.loads(script.string)
    except (json.JSONDecodeError, TypeError):
        return None
    return None

# --- NEW UNIVERSAL PRICE FUNCTION ---
def get_universal_price(element: BeautifulSoup | Tag) -> Optional[str]:
    """Tries multiple strategies to find a price within a given HTML element."""
    
    # 1. Try JSON-LD first (if we're looking at the whole page)
    if isinstance(element, BeautifulSoup):
        ld_data = get_data_from_json_ld(element)
        if ld_data:
            try:
                price = ld_data.get("offers", [{}])[0].get("price")
                if price:
                    return str(price)
            except (KeyError, IndexError):
                pass

    # 2. Use a broad set of smart selectors
    price_selectors = [
        '[itemprop="price"]', '[data-testid*="price"]', '[class*="price"]',
        '[class*="amount"]', '[id*="price"]', '.price', '.money', 
        '.product-price', '.product-information_price' # Added from Gymshark example
    ]
    for selector in price_selectors:
        price_el = element.select_one(selector)
        if price_el:
            price_text = price_el.get("content") or price_el.get_text(strip=True)
            cleaned = clean_price_string(price_text)
            if cleaned:
                return cleaned

    # 3. Fallback: Text-based search for currency symbols (last resort)
    price_pattern = re.compile(r"[\$\€\£\¥\₹]\s*\d+[\.,\d]*")
    potential_price = element.find(string=price_pattern)
    if potential_price:
        return clean_price_string(potential_price)
        
    return None

# Assumes you have the get_data_from_json_ld helper from the previous answer
# def get_data_from_json_ld(soup: BeautifulSoup | Tag) -> Optional[Dict]: ...


def get_universal_currency(element: BeautifulSoup | Tag) -> Optional[str]:
    """
    Tries multiple strategies to find the currency on a page or within an element.
    Returns a 3-letter ISO currency code (e.g., 'USD').
    """
    
    # 1. Highest Priority: Try to parse structured JSON-LD data
    if isinstance(element, BeautifulSoup):
        ld_data = get_data_from_json_ld(element)
        if ld_data:
            try:
                offers = ld_data.get("offers", {})
                # Handle if offers is a list or a single dictionary
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                
                currency = offers.get("priceCurrency")
                if currency and isinstance(currency, str) and len(currency) == 3:
                    return currency.upper()
            except (KeyError, IndexError, AttributeError):
                pass # Continue to the next method

    # 2. Second Priority: Check meta tags and microdata attributes
    meta_selectors = [
        'meta[property="product:price:currency"]',
        'meta[property="og:price:currency"]',
        '[itemprop="priceCurrency"]'
    ]
    for selector in meta_selectors:
        tag = element.select_one(selector)
        if tag and tag.get("content"):
            currency = tag["content"]
            if isinstance(currency, str) and len(currency) == 3:
                return currency.upper()

    # Get the text content once for the next two methods
    text_content = element.get_text(" ", strip=True)

    # 3. Third Priority: Find 3-letter currency codes (e.g., USD, INR) in the text
    # This is more reliable than just a symbol.
    common_codes = {'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'INR'}
    found_codes = re.findall(r'\b([A-Z]{3})\b', text_content)
    for code in found_codes:
        if code in common_codes:
            return code

    # 4. Last Resort: Map common currency symbols to codes
    # This is an assumption, as '$' could be many currencies, but it's a useful fallback.
    symbol_map = {
        '₹': 'INR',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '$': 'USD' # Defaulting '$' to USD
    }
    for symbol, code in symbol_map.items():
        if symbol in text_content:
            return code
            
    return None # Return None if all methods fail
