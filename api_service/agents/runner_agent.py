"""
Runner Agent — Report Writer
=============================
Takes raw SQL analytics data and generates a structured operational
investigation report in plain English using Gemini.
"""

import os
import json
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# gemini-flash-latest confirmed 200 OK; others as fallback
GEMINI_MODELS = ["gemini-flash-latest", "gemini-2.0-flash", "gemini-3.5-flash"]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_INSTRUCTION = """You are an Operational Intelligence Report Writer for an e-commerce platform called EcomIQ.

You receive raw analytics data (SQL query results + anomaly signals) and generate
a clear, concise operational investigation report.

Your report MUST follow this exact structure:

## 🔍 Investigation Summary
One sentence describing what was investigated and what the key finding is.

## 📊 Key Findings
- Bullet points of the most important numbers and facts from the data
- Focus on anomalies, spikes, and drops flagged in the signals
- Include actual numbers from the data

## ⚠️ Operational Signals
- List the detected anomalies (from the "signals" arrays in the data)
- Explain what each signal means in business terms

## 🧠 Root Cause Analysis
- Based on the data patterns, what is likely causing the issue?
- Connect the dots between different data sections

## 📈 Operational Impact
- What business impact does this have?
- Which customers / regions / products are affected?

## ✅ Recommended Actions
- 3-5 concrete, actionable recommendations
- Be specific (e.g., "Audit Delhivery courier routes in West India")

Rules:
- Be concise and professional
- Use actual numbers from the data
- If the data shows no anomalies, clearly state that operations look healthy
- Do NOT invent data that isn't in the provided analytics
"""


class RunnerAgent:
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
                    r = httpx.post(url, headers=self.headers, json=payload, timeout=60.0)
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

    def generate_report(self, user_query: str, scope: dict, analytics_data: dict) -> str:
        """Generate a human-readable investigation report from raw analytics data."""

        prompt = f"""
User Question: {user_query}

Investigation Scope Applied: {json.dumps(scope, indent=2)}

Raw Analytics Data:
{json.dumps(analytics_data, indent=2, default=str)}

Please generate a full operational investigation report based on this data.
"""

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
            }
        }

        data = self._call_gemini(payload)
        return data["candidates"][0]["content"]["parts"][0]["text"]
