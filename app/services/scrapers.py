from typing import List, Dict, Optional
import httpx
from bs4 import Tag
from app.models import (
    BrandContext, Product, FAQ, Policies,
    SocialHandles, ContactDetails, ImportantLinks
)

from .helpers import get_universal_price, get_universal_currency
from .helpers import (
    norm_base, fetch_text, fetch_json, soup, is_shopify_html, absolute,
    EMAIL_RE, PHONE_RE
)

# ---------- Product catalog with PAGINATION ----------
async def get_products(client: httpx.AsyncClient, base: str) -> List[Product]:
    products: List[Product] = []
    
    # We will use one of these URLs as a template
    candidate_urls = [
        f"{base}/products.json?limit=250",
        f"{base}/collections/all/products.json?limit=250",
    ]

    for url_template in candidate_urls:
        page = 1
        while True:  # Loop until we run out of pages
            try:
                paginated_url = f"{url_template}&page={page}"
                data = await fetch_json(client, paginated_url)
                items = data.get("products") or data.get("items") or []

                if not items:
                    # If we get an empty list, it's the last page.
                    break 

                for p in items:
                    # Your original, robust data extraction logic is great here!
                    variants = p.get("variants", [])
                    price = (variants[0].get("price") or variants[0].get("cost") or variants[0].get("amount") or variants[0].get("value")) if variants else None
                    currency = variants[0].get("currency") or p.get("currency") if variants else None
                    images = p.get("images") or []
                    raw_img = (images[0].get("src") if images else None) or (p.get("image") or {}).get("src")
                    image = absolute(base, raw_img) if raw_img else None
                    handle = p.get("handle")
                    prod_url = absolute(base, f"/products/{handle}") if handle else None

                    products.append(Product(
                        title=p.get("title") or "", handle=handle, url=prod_url,
                        price=str(price) if price is not None else None,
                        currency=currency, image=image, tags=p.get("tags", [])
                    ))
                
                page += 1 # Increment to get the next page
            
            except Exception:
                # If any page fails, just stop trying for that URL template
                break
        
        # If we successfully got products from the first candidate URL, we don't need to try the second.
        if products:
            break

    # De-duplicate by handle/title (your original logic is perfect)
    seen = set()
    deduped = []
    for p in products:
        key = (p.handle or "").lower() or (p.title or "").lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(p)
    return deduped

# ---------- Hero products from homepage ----------
def extract_hero_products(home_soup, base: str) -> List[Product]:
    heroes: List[Product] = []
    # Find all product cards instead of just links for a more stable context
    for card in home_soup.select('[class*="product-card"], [class*="product-item"]'):
        link_el = card.select_one('a[href*="/products/"]')
        if not link_el:
            continue
            
        href = absolute(base, link_el.get("href"))
        title = (link_el.get("title") or link_el.get_text(strip=True)) or "Hero product"

        # Use the universal helper to find the price within the card
        price = get_universal_price(card) 
        currency = get_universal_currency(card)
        img = card.select_one("img")
        raw_img = img.get("src") if img else None
        image = absolute(base, raw_img) if raw_img else None

        if href and "/products/" in href:
            heroes.append(Product(
                title=title,
                url=href,
                image=image,
                price=price,
                currency=currency
            ))

    # Deduplicate by URL
    uniq = {}
    for h in heroes:
        if h.url and h.url not in uniq:
            uniq[h.url] = h
    return list(uniq.values())[:12]

# ---------- Policies ----------
def find_policy_links(home_soup, base: str) -> Policies:
    candidates = {
        "privacy_policy_url": ["/policies/privacy-policy", "/pages/privacy-policy", "/privacy-policy", "/policies/privacy"],
        "refund_policy_url": ["/policies/refund-policy", "/pages/refund-policy", "/refund-policy", "/policies/refunds"],
        "terms_url":          ["/policies/terms-of-service", "/pages/terms-of-service", "/terms-of-service", "/terms"],
        "shipping_policy_url":["/policies/shipping-policy", "/pages/shipping-policy", "/shipping-policy", "/policies/shipping"],
    }
    found = {}

    # 1) Direct candidates
    for key, paths in candidates.items():
        for p in paths:
            link = home_soup.select_one(f'a[href$="{p}"], a[href*="{p}"]')
            if link:
                found[key] = absolute(base, link.get("href"))
                break

    # 2) Fallback: footer text search
    footer = home_soup.find("footer")
    anchor_scope = footer or home_soup
    for a in anchor_scope.find_all("a"):
        text = (a.get_text() or "").strip().lower()
        href = absolute(base, a.get("href"))
        if not href: 
            continue
        if "privacy" in text and "privacy_policy_url" not in found:
            found["privacy_policy_url"] = href
        if ("refund" in text or "returns" in text) and "refund_policy_url" not in found:
            found["refund_policy_url"] = href
        if "terms" in text and "terms_url" not in found:
            found["terms_url"] = href
        if "shipping" in text and "shipping_policy_url" not in found:
            found["shipping_policy_url"] = href

    return Policies(**found)

# ---------- FAQs ----------
def extract_faqs(doc, base: str) -> List[FAQ]:
    faqs: List[FAQ] = []

    # <details><summary>
    for d in doc.select("details"):
        q = d.find("summary")
        a = d.find("div") or d.find("p")
        qtxt = q.get_text(" ", strip=True) if q else ""
        atxt = a.get_text(" ", strip=True) if a else d.get_text(" ", strip=True)
        if qtxt and atxt:
            faqs.append(FAQ(question=qtxt, answer=atxt))

    # Heading + paragraphs
    headings = doc.select("h1, h2, h3, h4")
    for h in headings:
        q = h.get_text(" ", strip=True)
        cur = h.next_sibling
        answer_chunks = []
        while cur and getattr(cur, "name", None) not in {"h1","h2","h3","h4"}:
            if getattr(cur, "name", None) in {"p","div","li"}:
                answer_chunks.append(cur.get_text(" ", strip=True))
            cur = cur.next_sibling
        atxt = " ".join([c for c in answer_chunks if c]).strip()
        if q and atxt:
            faqs.append(FAQ(question=q, answer=atxt))

    # Dedup
    uniq = set()
    cleaned = []
    for f in faqs:
        key = (f.question[:80].lower(), f.answer[:120].lower())
        if key not in uniq:
            uniq.add(key)
            cleaned.append(f)
    return cleaned[:50]

# ---------- Socials ----------
def extract_socials(doc, base: str) -> SocialHandles:
    sh = {}
    for a in doc.find_all("a", href=True):
        href = absolute(base, a["href"])
        low = href.lower()
        if "instagram.com" in low and "instagram" not in sh: sh["instagram"] = href
        elif ("facebook.com" in low or "fb.me/" in low) and "facebook" not in sh: sh["facebook"] = href
        elif "tiktok.com" in low and "tiktok" not in sh: sh["tiktok"] = href
        elif "twitter.com" in low or "x.com" in low:
            if "twitter" not in sh: sh["twitter"] = href
        elif "youtube.com" in low or "youtu.be" in low:
            if "youtube" not in sh: sh["youtube"] = href
        elif "linkedin.com" in low and "linkedin" not in sh: sh["linkedin"] = href
        elif "pinterest.com" in low and "pinterest" not in sh: sh["pinterest"] = href

    others = {}
    return SocialHandles(**sh, others=others)

# ---------- Contacts ----------
def extract_contacts(doc) -> ContactDetails:
    text = doc.get_text(" ", strip=True)
    emails = sorted(set(EMAIL_RE.findall(text)))
    phones = sorted(set(PHONE_RE.findall(text)))
    return ContactDetails(emails=emails[:10], phones=phones[:10])

# ---------- About & Important links ----------
def find_about_and_links(home_soup, base: str):
    about_text = None
    imp = {}
    scope = home_soup.find("footer") or home_soup
    for a in scope.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        href = absolute(base, a["href"])
        if not href:
            continue
        if not about_text and ("about" in txt or "our story" in txt):
            try:
                # defer actual fetching to caller
                pass
            except Exception:
                pass
        if ("track" in txt or "order tracking" in txt or "track order" in txt) and "order_tracking" not in imp:
            imp["order_tracking"] = href
        if ("contact" in txt) and "contact_us" not in imp:
            imp["contact_us"] = href
        if ("blog" in txt or "/blogs" in href) and "blog" not in imp:
            imp["blog"] = href
    return about_text, ImportantLinks(**imp)

# ---------- Main orchestrator ----------
async def fetch_brand_context(website_url: str) -> BrandContext:
    base = norm_base(website_url)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        home_html = ""
        try:
            home_html = await fetch_text(client, base)
        except Exception:
            return BrandContext(is_shopify=False, base_url=base)

        doc = soup(home_html)
        is_shopify = is_shopify_html(home_html)

        # Brand name
        brand_name = None
        title = doc.find("title")
        if title: brand_name = title.get_text(strip=True)
        og_site = doc.find("meta", {"property":"og:site_name"})
        if og_site and og_site.get("content"): brand_name = og_site["content"]

        # Catalog
        product_catalog = await get_products(client, base)

        # Hero products
        hero_products = extract_hero_products(doc, base)

        # Policies
        policies = find_policy_links(doc, base)

        # FAQs
        faqs: List[FAQ] = []
        faq_pages = set()
        for a in doc.find_all("a", href=True):
            href = a["href"].lower()
            if "faq" in href or "faqs" in href or "/pages/help" in href or "/pages/support" in href:
                faq_pages.add(absolute(base, a["href"]))
        faq_pages.update([f"{base}/pages/faq", f"{base}/pages/faqs", f"{base}/apps/faq"])
        for page in list(faq_pages)[:5]:
            try:
                html = await fetch_text(client, page)
                faqs.extend(extract_faqs(soup(html), base))
            except Exception:
                continue
        seen = set()
        faqs_clean = []
        for f in faqs:
            key = (f.question[:80].lower(), f.answer[:120].lower())
            if key not in seen:
                seen.add(key)
                faqs_clean.append(f)

        # Socials, contacts
        social_handles = extract_socials(doc, base)
        contact_details = extract_contacts(doc)

        # About & links
        about_text, important_links = find_about_and_links(doc, base)
        if about_text is None:
            for path in ["/pages/about", "/pages/about-us", "/about-us", "/about", "/pages/our-story"]:
                try:
                    html = await fetch_text(client, f"{base}{path}")
                    about_text = soup(html).get_text(" ", strip=True)[:2000]
                    if about_text and len(about_text) > 60:
                        break
                except Exception:
                    continue

        # Policies fallback
        async def fill_policy(url_attr, candidates):
            if getattr(policies, url_attr, None):
                return
            for p in candidates:
                try:
                    html = await fetch_text(client, f"{base}{p}")
                    if html:
                        setattr(policies, url_attr, f"{base}{p}")
                        break
                except Exception:
                    continue

        await fill_policy("privacy_policy_url", ["/policies/privacy-policy"])
        await fill_policy("refund_policy_url",  ["/policies/refund-policy"])
        await fill_policy("terms_url",          ["/policies/terms-of-service"])
        await fill_policy("shipping_policy_url",["/policies/shipping-policy"])

        return BrandContext(
            is_shopify=is_shopify,
            brand_name=brand_name,
            base_url=base,
            product_catalog=product_catalog,
            hero_products=hero_products,
            policies=policies,
            faqs=faqs_clean,
            social_handles=social_handles,
            contact_details=contact_details,
            about_text=about_text,
            important_links=important_links
        )
