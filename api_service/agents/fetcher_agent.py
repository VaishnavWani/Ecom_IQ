"""
Fetcher Agent — Scope Extractor
================================
Reads a natural language question and extracts structured scope parameters
that are then used to filter the analytics engine queries.

Example:
    Input:  "Why is Delhivery performing poorly in West India?"
    Output: {"region": "West India", "courier_name": "Delhivery"}
"""

import os
import re
import json
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# gemini-flash-latest confirmed 200 OK; others as fallback
GEMINI_MODELS = ["gemini-flash-latest", "gemini-2.0-flash", "gemini-3.5-flash"]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_INSTRUCTION = """You are an Operational Scope Extraction Agent for an e-commerce analytics system.

Your ONLY job is to read a user's question and extract investigation parameters (scope)
that will be used to filter database queries.

You DO NOT analyse data. You DO NOT explain anything.
You ONLY return a JSON object with relevant filter parameters.

Available scope parameters (only include ones mentioned in the query):

  region         → "West India" | "North India" | "South India" | "East India"
  city           → "Mumbai" | "Delhi" | "Bangalore" | "Chennai" | "Pune" | "Jaipur" | "Kolkata"
  courier_name   → "Delhivery" | "BlueDart" | "EcomExpress" | "DTDC"
  payment_status → "success" | "failed"
  payment_method → "UPI" | "Credit Card" | "Debit Card"
  device_type    → "mobile" | "desktop" | "tablet"
  return_reason  → "damaged" | "wrong_item" | "not_needed" | "size_issue"
  category       → "Electronics" | "Apparel" | "Home"

Rules:
- Return ONLY valid JSON. No markdown, no explanation.
- Include ONLY parameters explicitly mentioned.
- If nothing specific is mentioned, return {}.
- Map user intent: "deliveries" → courier_name if courier mentioned, "mobile users" → device_type: "mobile"
"""


class FetcherAgent:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _call_gemini(self, payload: dict) -> dict:
        """Try each model in fallback chain; retry on 429/503."""
        last_err = None
        for model in GEMINI_MODELS:
            url = f"{GEMINI_BASE}/{model}:generateContent"
            for attempt in range(3):  # up to 3 retries per model
                try:
                    r = httpx.post(url, headers=self.headers, json=payload, timeout=30.0)
                    if r.status_code in (429, 503):
                        wait = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                        time.sleep(wait)
                        continue
                    r.raise_for_status()
                    return r.json()
                except httpx.HTTPStatusError as e:
                    last_err = e
                    code = e.response.status_code
                    if code not in (429, 503):
                        break  # hard error — try next model
                    time.sleep(2 ** attempt)
        raise last_err

    def extract_scope(self, user_query: str) -> dict:
        """Extract structured scope parameters from a natural language query."""
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"Extract scope from this query: {user_query}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
            }
        }

        data = self._call_gemini(payload)
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Strip markdown fences if present
        cleaned = re.sub(r"```json|```", "", raw_text).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {}
