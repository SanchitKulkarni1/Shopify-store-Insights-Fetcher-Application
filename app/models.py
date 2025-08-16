# app/models.py

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict

# ✨ Added the missing FetchRequest model needed by main.py
class FetchRequest(BaseModel):
    website_url: HttpUrl

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
    # ✨ Changed to use default_factory for clarity and safety
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
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
    # ✨ Changed to use default_factory
    others: Dict[str, str] = Field(default_factory=dict)

class ImportantLinks(BaseModel):
    order_tracking: Optional[str] = None
    contact_us: Optional[str] = None
    blog: Optional[str] = None
    # ✨ Changed to use default_factory
    others: Dict[str, str] = Field(default_factory=dict)

class BrandContext(BaseModel):
    is_shopify: bool
    brand_name: Optional[str] = None
    base_url: str

    # ✨ Changed all mutable and nested model defaults to use Field(default_factory=...)
    product_catalog: List[Product] = Field(default_factory=list)
    hero_products: List[Product] = Field(default_factory=list)

    policies: Policies = Field(default_factory=Policies)
    faqs: List[FAQ] = Field(default_factory=list)
    social_handles: SocialHandles = Field(default_factory=SocialHandles)
    contact_details: ContactDetails = Field(default_factory=ContactDetails)
    about_text: Optional[str] = None
    important_links: ImportantLinks = Field(default_factory=ImportantLinks)