import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from app.models import BrandContext

# Load and configure the API
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found.")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

def get_target_schema() -> str:
    """Generates a JSON string of the BrandContext schema."""
    schema = BrandContext.model_json_schema()
    return json.dumps(schema, indent=2)

async def structure_data_with_gemini(raw_data: dict) -> dict:
    """
    Uses Gemini to intelligently clean and structure brand info,
    focusing on refining the About Us text and FAQs.
    """
    target_schema = get_target_schema()
    raw_data_json = json.dumps(raw_data, indent=2)

    # ✨ THIS PROMPT IS NOW MUCH SMARTER
    prompt = f"""
    You are an expert data cleaning and extraction API. Your task is to analyze the provided raw JSON data and meticulously structure it according to the target schema.

    Follow these critical rules:
    1.  **For the 'about_text' field:** Find the section that describes the company. Extract ONLY the narrative paragraphs. EXCLUDE all surrounding text like "Skip to content," sale announcements, product categories, navigation links (e.g., 'Home', 'Contact us'), and any other menu-like items. The result must be a clean, readable block of text.
    2.  **For the 'faqs' field:** Analyze the raw FAQ data. Identify and extract ONLY legitimate question-and-answer pairs. Discard any items that are actually navigation links, headers, or other non-FAQ text (like 'DIY HAIR EXTENSIONS', 'Information', 'Quick link'). Each item in the final list must be a genuine FAQ.
    3.  **General:** The final output MUST be a single, valid JSON object that strictly adheres to the schema. Do not add any extra text or explanations.

    ## Target JSON Schema:
    ```json
    {target_schema}
    ```

    ## Raw Input Data:
    ```json
    {raw_data_json}
    ```

    ## Structured JSON Output:
    """
    try:
        config = genai.types.GenerationConfig(
            max_output_tokens=8192,
            response_mime_type="application/json"
        )
        response = await model.generate_content_async(prompt, generation_config=config)
        cleaned_json = json.loads(response.text)
        return cleaned_json
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"--- BROKEN GEMINI RESPONSE ---\n{response.text}\n--- END OF RESPONSE ---")
        raise ValueError(f"Failed to process data with Gemini: {e}")