import json
import httpx
from datetime import date
from pydantic import ValidationError

from app.config import settings
from app.schemas.expense import ExpenseParseResult

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={{}}"


async def call_gemini(system_prompt: str, user_prompt: str, image_part: dict = None) -> dict:
    url = GEMINI_API_URL.format(settings.gemini_api_key)
    
    parts = [{"text": user_prompt}]
    if image_part:
        parts.insert(0, image_part)
        
    payload = {
        "contents": [
            {
                "parts": parts
            }
        ],
        "systemInstruction": {
            "parts": [
                {
                    "text": system_prompt
                }
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }
    
    # generate_weekly_insight expects plain text
    if not image_part and "friendly personal finance assistant" in system_prompt:
        payload["generationConfig"]["responseMimeType"] = "text/plain"
        payload["generationConfig"]["temperature"] = 0.7

    async with httpx.AsyncClient() as client:
        try:
            print(f"[AI SERVICE] Calling Gemini API for: {user_prompt[:60]}...")
            resp = await client.post(url, json=payload, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            
            # Extract text from parts (handling thinking models that return multiple parts)
            candidate = data["candidates"][0]
            if "content" not in candidate or "parts" not in candidate.get("content", {}):
                print(f"[AI SERVICE] Response blocked: {candidate.get('finishReason')}")
                return {"success": False, "error": f"Blocked: {candidate.get('finishReason')}", "text": ""}
                
            content_parts = candidate["content"]["parts"]
            
            # Get the LAST text part (thinking models put reasoning first, answer last)
            text = ""
            for part in reversed(content_parts):
                if "text" in part:
                    text = part["text"]
                    break
            
            print(f"[AI SERVICE] Success. Response length: {len(text)}")
            return {"success": True, "text": text, "raw": data}
        except Exception as e:
            print(f"[AI SERVICE] Gemini API error: {type(e).__name__}: {e}")
            return {"success": False, "error": str(e), "text": ""}


async def parse_voice_transcript(transcript: str, user_currency: str) -> dict:
    today_date = date.today().isoformat()
    
    system_prompt = f"""You are a financial expense parser. Extract expense details from natural language.
Always respond with valid JSON only. No explanation, no markdown, no preamble.

Available categories: Food, Transport, Entertainment, Rent, Shopping, Health, Education, Electricity, Utilities, Miscellaneous

Response format:
{{
  "amount": <number>,
  "currency": "<3-letter currency code, default to user_currency if not mentioned>",
  "category": "<one of the available categories>",
  "description": "<clean 2-5 word description>",
  "merchant": "<merchant name if mentioned, else null>",
  "expense_date": "<YYYY-MM-DD, today if not mentioned>",
  "confidence": <0.0 to 1.0>,
  "notes": "<any extra context worth saving, else null>"
}}

Rules:
- For amounts, extract numbers from words (e.g. "eight hundred" = 800)
- If the transcript is unclear or not an expense, set confidence below 0.5
- Today's date is {today_date}
- User's default currency is {user_currency}
"""
    
    fallback = {
        "amount": 0.0,
        "currency": user_currency,
        "category": "Miscellaneous",
        "description": "Unparsed expense",
        "merchant": None,
        "expense_date": today_date,
        "confidence": 0.1,
        "notes": None
    }
    
    try:
        print(f"[AI SERVICE] Parsing voice transcript: '{transcript}'")
        result = await call_gemini(system_prompt, transcript)
        
        if not result["success"]:
            print(f"[AI SERVICE] Gemini call failed: {result.get('error')}")
            return fallback
            
        text = result["text"]
        parsed_json = json.loads(text)
        print(f"[AI SERVICE] Parsed: amount={parsed_json.get('amount')}, category={parsed_json.get('category')}")
        
        # Validate through Pydantic
        ExpenseParseResult(**parsed_json)
        return parsed_json
        
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"[AI SERVICE] Parse/validation error: {e}")
        return fallback
    except Exception as e:
        print(f"[AI SERVICE] Unexpected error: {type(e).__name__}: {e}")
        return fallback


async def parse_receipt_image(image_base64: str, mime_type: str, user_currency: str) -> dict:
    today_date = date.today().isoformat()
    
    system_prompt = f"""You are a receipt parser. Analyse this receipt image and extract expense details.
Always respond with valid JSON only. No explanation, no markdown, no preamble.

Available categories: Food, Transport, Entertainment, Rent, Shopping, Health, Education, Electricity, Utilities, Miscellaneous

Response format:
{{
  "amount": <total amount as number>,
  "currency": "<currency from receipt or user_currency>",
  "category": "<best matching category>",
  "description": "<merchant name or receipt type, 2-5 words>",
  "merchant": "<merchant/store name>",
  "expense_date": "<YYYY-MM-DD from receipt date, or today>",
  "confidence": <0.0 to 1.0>,
  "notes": "<itemised summary if useful, else null>"
}}

If the image is not a receipt, return confidence: 0.1
User's default currency is {user_currency}
"""

    image_part = {
        "inlineData": {
            "mimeType": mime_type,
            "data": image_base64
        }
    }

    result = await call_gemini(system_prompt, "Parse this receipt.", image_part=image_part)
    
    fallback = {
        "amount": 0.0,
        "currency": user_currency,
        "category": "Miscellaneous",
        "description": "Unparsed receipt",
        "merchant": None,
        "expense_date": today_date,
        "confidence": 0.1,
        "notes": None
    }
    
    if not result["success"]:
        return fallback
        
    try:
        parsed_json = json.loads(result["text"])
        ExpenseParseResult(**parsed_json)
        return parsed_json
    except (json.JSONDecodeError, ValidationError):
        return fallback


async def generate_weekly_insight(user_id, week_data: dict) -> str:
    system_prompt = """You are a friendly personal finance assistant. Write a 3-4 sentence weekly spending insight.
Be conversational, not preachy. Include specific numbers. Highlight one positive and one area to watch.
Respond in plain text only."""
    
    user_prompt = f"Data: {json.dumps(week_data)}"
    
    result = await call_gemini(system_prompt, user_prompt)
    if not result["success"]:
        return "You had some activity this week. Keep tracking your expenses to see detailed insights."
        
    return result["text"].strip()
