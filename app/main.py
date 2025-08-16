from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, AnyUrl
from app.models import BrandContext
from .services.scrapers import fetch_brand_context
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Shopify Insights Fetcher")

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ In production, replace with ["http://localhost:5173"] or your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FetchRequest(BaseModel):
    website_url: AnyUrl

@app.post("/fetch-insights", response_model=BrandContext)
async def fetch_insights(req: FetchRequest):
    try:
        data = await fetch_brand_context(str(req.website_url))
        if not data.is_shopify:
            # Spec says 401 when website not found
            raise HTTPException(status_code=401, detail="Website not found or not a Shopify store")
        return data
    except HTTPException:
        raise
    except Exception as e:
        # Hide internals in prod
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
