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

async def generate_financial_insights(user_id: str, currency: str, transactions_data: list, budgets_data: list) -> list:
    system_prompt = f"""You are an elite, highly analytical personal finance AI. 
Analyze the provided user's transactions and budgets for the current month.
Return a JSON array of exactly 5 insight objects. Each object must have:
- "type": either "trend", "optimization", "praise", or "warning"
- "title": a short 3-5 word concise title
- "message": a 2-3 sentence actionable insight with specific numbers.
Ensure all monetary values use the {currency} currency symbol appropriately.

CRITICAL INSTRUCTIONS:
1. DIFFERENTIATE FIXED VS. FLEXIBLE COSTS: You MUST understand the difference between recurring monthly bills (like 'Rent', 'Utilities', 'Subscription', 'Electricity') and discretionary purchases. Do NOT refer to paying 'Rent' or a utility bill as a "splurge", "significant purchase", "shopping spree", or discretionary expense. They are fixed costs. Ignore fixed costs when advising on areas to cut back.
2. If there are noticeable high burns or single massive discretionary transactions, output ONE OR TWO of the following exact insight patterns mathematically:
   - "High Spending Velocity": E.g., "You're burning through {currency}X/day. At this pace, you'll exceed your monthly budget by {currency}Y."
   - "Major Splurge Detected": E.g., "Your recent purchase at [Merchant] consumed Y% of your entire monthly budget in one go!"
   - "Excellent Trajectory": E.g., "You're on track to save an impressive {currency}X this month!"
   - "Spending Down": E.g., "Great job! Your spending is tracking lower than last month."
3. You MUST analyze EXACT "merchant" names and specific patterns from the transaction data. Provide exact mathematical breakdowns that mention real merchant names from their data.

Do not use markdown. Return ONLY the valid JSON array. For example ({currency} example):
[
  {{"type": "warning", "title": "High Spending Velocity", "message": "You're burning through {currency}200/day. At this pace, you'll exceed your monthly budget by {currency}14,000."}},
  {{"type": "warning", "title": "Major Splurge Detected", "message": "Your recent purchase at 'Apple' consumed 27% of your entire monthly budget in one go!"}},
  {{"type": "praise", "title": "Great Grocery Pacing", "message": "You have kept Food spending to just 10% of your limit, primarily shopping efficiently at 'Whole Foods'."}},
  {{"type": "optimization", "title": "Coffee Habit Drain", "message": "You visited 'Starbucks' 4 times. Making coffee at home could save you roughly {currency}45 next week."}},
  {{"type": "praise", "title": "Excellent Trajectory", "message": "You're on track to save an impressive {currency}400 this month! Your daily burn rate is remarkably efficient."}}
]
"""
    
    data_context = {
        "transactions": transactions_data,
        "budgets": budgets_data
    }
    user_prompt = f"Data: {json.dumps(data_context, default=str)}"
    
    result = await call_gemini(system_prompt, user_prompt)
    if not result["success"]:
        return []
    
    try:
        import re
        data = result["text"].strip()
        
        # Regex pull the array out safely
        match = re.search(r'\[.*\]', data, re.DOTALL)
        if match:
            data = match.group(0)
            
        return json.loads(data)
    except Exception as e:
        print(f"[AI SERVICE] Failed to parse financial insights array: {e}\nRaw: {result['text']}")
        return []
