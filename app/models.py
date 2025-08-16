from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict

class Product(BaseModel):
    title: str
    handle: Optional[str] = None
    url: Optional[HttpUrl] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    image: Optional[HttpUrl] = None
    tags: Optional[List[str]] = None

class FAQ(BaseModel):
    question: str
    answer: str

class ContactDetails(BaseModel):
    emails: List[str] = []
    phones: List[str] = []
    address: Optional[str] = None

class Policies(BaseModel):
    privacy_policy_url: Optional[str] = None
    refund_policy_url: Optional[str] = None
    terms_url: Optional[str] = None
    shipping_policy_url: Optional[str] = None

class SocialHandles(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    tiktok: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    linkedin: Optional[str] = None
    pinterest: Optional[str] = None
    others: Dict[str, str] = {}

class ImportantLinks(BaseModel):
    order_tracking: Optional[str] = None
    contact_us: Optional[str] = None
    blog: Optional[str] = None
    others: Dict[str, str] = {}

class BrandContext(BaseModel):
    is_shopify: bool
    brand_name: Optional[str] = None
    base_url: str

    product_catalog: List[Product] = []
    hero_products: List[Product] = []

    policies: Policies = Policies()
    faqs: List[FAQ] = []
    social_handles: SocialHandles = SocialHandles()
    contact_details: ContactDetails = ContactDetails()
    about_text: Optional[str] = None
    important_links: ImportantLinks = ImportantLinks()
