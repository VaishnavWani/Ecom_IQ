"""Runs inside Docker to list available Gemini models and pick the right one."""
import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY", "")
print(f"Key prefix: {api_key[:10]}...")

client = genai.Client(api_key=api_key)

print("\nAvailable models that support generateContent:")
try:
    for m in client.models.list():
        if hasattr(m, 'supported_actions') and 'generateContent' in str(m.supported_actions):
            print(f"  {m.name}")
        elif hasattr(m, 'name'):
            print(f"  {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

# Try a quick generateContent test on common model names
test_models = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite", 
    "gemini-2.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
]

print("\nTesting which models work:")
for model in test_models:
    try:
        r = client.models.generate_content(model=model, contents="Say hi in one word")
        print(f"  ✅ {model}  →  {r.text.strip()[:30]}")
        break  # stop at first working one
    except Exception as e:
        err = str(e)[:80]
        print(f"  ❌ {model}  →  {err}")
