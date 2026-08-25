import os
from typing import Any, Optional, Union
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class ParseResult(BaseModel):
    job_type: Optional[str] = Field(default=None, description="The job type code, matched strictly to one of the provided job type codes.")
    area_m2: Optional[float] = Field(default=None, description="The area/size value in square meters.")
    region: Optional[str] = Field(default=None, description="The region code, matched strictly to one of the provided region codes.")
    confidence: bool = Field(description="True if both job_type and area_m2 were successfully parsed and matched, False otherwise.")

def get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def parse_free_text(text: str, job_types: list[dict[str, str]], regions: list[dict[str, str]]) -> dict[str, Any]:
    """
    Parses free text using Gemini API into structured JSON with job_type, area_m2, and region.
    """
    client = get_genai_client()
    if not client:
        return {"job_type": None, "area_m2": None, "region": None, "confidence": False}

    job_types_str = ", ".join([f"'{jt['code']}' ({jt['name']})" for jt in job_types])
    regions_str = ", ".join([f"'{r['code']}' ({r['name']})" for r in regions])

    system_instruction = (
        "You are an assistant parsing home renovation requests in Polish or Ukrainian. "
        "Extract the type of renovation work, the area in square meters (m²), and the region. "
        f"The valid job types are: {job_types_str}. "
        f"The valid region codes are: {regions_str}. "
        "If the user specifies dimensions (e.g. 2x2 or 2 by 3 meters), calculate the area (4m² or 6m² respectively). "
        "Return the extracted values as structured JSON according to the schema. "
        "If you cannot determine the job type or the area with high confidence, set confidence=false."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=text,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ParseResult,
                system_instruction=system_instruction,
                temperature=0.0,
            ),
        )
        import json
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"Gemini API error during parse: {e}")
        return {"job_type": None, "area_m2": None, "region": None, "confidence": False}

def generate_estimate_summary(estimate_data: dict[str, Any], locale: str = "pl") -> Optional[str]:
    """
    Generates a natural-language friendly summary of the structured estimate.
    """
    client = get_genai_client()
    if not client:
        return None

    job_name = estimate_data.get("job_name")
    area = estimate_data.get("area_m2")
    total_price = estimate_data.get("total_price")
    duration = estimate_data.get("estimated_duration_days")
    currency = estimate_data.get("currency")
    materials_total = estimate_data.get("materials_total")
    works_total = estimate_data.get("works_total")

    prompt = (
        f"Przedstaw zwięzłe, przyjazne podsumowanie wyceny dla klienta.\n"
        f"Rodzaj prac: {job_name}\n"
        f"Powierzchnia: {area} m²\n"
        f"Koszt materiałów: {materials_total} {currency}\n"
        f"Koszt robocizny: {works_total} {currency}\n"
        f"Razem koszt: {total_price} {currency}\n"
        f"Szacowany czas: {duration} dni\n\n"
        f"Napisz krótki, zachęcający tekst (maksymalnie 3-4 zdania) w języku {locale}, "
        f"który podsumuje te koszty i czas wykonania."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error during summary generation: {e}")
        return None
