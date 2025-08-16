import re
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

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
