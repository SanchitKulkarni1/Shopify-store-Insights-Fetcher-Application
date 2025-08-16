from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, AnyUrl
from app.models import BrandContext
from .services.scrapers import fetch_brand_context

app = FastAPI(title="Shopify Insights Fetcher")

class FetchRequest(BaseModel):
    website_url: AnyUrl

@app.post("/fetch-insights", response_model=BrandContext)
async def fetch_insights(req: FetchRequest):
    try:
        data = await fetch_brand_context(str(req.website_url))
        if not data.is_shopify:
            # Spec says 401 when website not found (we’ll treat “not Shopify/invalid” as that)
            raise HTTPException(status_code=401, detail="Website not found or not a Shopify store")
        return data
    except HTTPException:
        raise
    except Exception as e:
        # Don’t leak stacktraces in prod; good enough for assignment
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
