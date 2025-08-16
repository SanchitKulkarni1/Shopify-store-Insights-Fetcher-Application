from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from app.models import BrandContext, FetchRequest
from app.services.scrapers import fetch_brand_context
from app.services.gemini_service import structure_data_with_gemini
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Shopify Insights Fetcher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/fetch-insights", response_model=BrandContext)
async def fetch_insights(req: FetchRequest):
    try:
        # 1. Scrape the raw data
        print(f"Starting scrape for: {req.website_url}")
        raw_data_object = await fetch_brand_context(str(req.website_url))
        raw_data_dict = raw_data_object.model_dump(mode='json')

        if not raw_data_dict.get("is_shopify"):
            raise HTTPException(status_code=401, detail="Website not found or not a Shopify store")

        # 2. ✨ SEPARATE the data
        # Store the original, raw product catalog in a separate variable
        original_product_catalog = raw_data_dict.get("product_catalog", [])
        
        # Now remove it so we can send the smaller data package to Gemini
        raw_data_dict.pop("product_catalog", None)
        raw_data_dict.pop("hero_products", None)

        # 3. ✨ Get the CLEAN brand info from Gemini
        print("Structuring brand info (FAQs, About Us, etc.) with Gemini...")
        structured_brand_info = await structure_data_with_gemini(raw_data_dict)

        # 4. ✨ RECOMBINE the data
        # Take the clean brand info from Gemini and add the original, raw product catalog back.
        final_data = structured_brand_info
        final_data["product_catalog"] = original_product_catalog

        # 5. Validate the final combined data and return
        print("Validating final data structure...")
        validated_data = BrandContext(**final_data)
        
        print("Process complete. Returning data.")
        return validated_data

    except ValidationError as e:
        print(f"VALIDATION ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"LLM output validation failed: {e}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")