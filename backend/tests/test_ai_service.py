import pytest
from unittest.mock import patch
from app.services.ai_service import parse_voice_transcript, parse_receipt_image

@pytest.mark.asyncio
@patch('app.services.ai_service.call_gemini')
async def test_parse_simple_voice_transcript(mock_call):
    mock_call.return_value = {
        "success": True,
        "text": '{"amount": 350, "currency": "INR", "category": "Food", "description": "lunch at Subway", "merchant": "Subway", "expense_date": "2024-03-01", "confidence": 0.95, "notes": null}'
    }
    
    result = await parse_voice_transcript("spent 350 on lunch at Subway", "INR")
    assert result["amount"] == 350
    assert result["category"] == "Food"

@pytest.mark.asyncio
@patch('app.services.ai_service.call_gemini')
async def test_parse_amount_in_words(mock_call):
    mock_call.return_value = {
        "success": True,
        "text": '{"amount": 800, "currency": "INR", "category": "Food", "description": "Groceries", "merchant": null, "expense_date": "2024-03-01", "confidence": 0.9, "notes": null}'
    }
    result = await parse_voice_transcript("eight hundred for groceries", "INR")
    assert result["amount"] == 800

@pytest.mark.asyncio
@patch('app.services.ai_service.call_gemini')
async def test_parse_ambiguous_transcript_low_confidence(mock_call):
    mock_call.return_value = {
        "success": True,
        "text": '{"amount": 0, "currency": "INR", "category": "Miscellaneous", "description": "Unclear", "merchant": null, "expense_date": "2024-03-01", "confidence": 0.2, "notes": null}'
    }
    result = await parse_voice_transcript("hello is this working", "INR")
    assert result["confidence"] <= 0.5

@pytest.mark.asyncio
@patch('app.services.ai_service.call_gemini')
async def test_parse_receipt_image(mock_call):
    mock_call.return_value = {
        "success": True,
        "text": '{"amount": 120.50, "currency": "USD", "category": "Shopping", "description": "Target haul", "merchant": "Target", "expense_date": "2024-03-01", "confidence": 0.98, "notes": null}'
    }
    result = await parse_receipt_image("base64data", "image/jpeg", "USD")
    assert result["amount"] == 120.50
