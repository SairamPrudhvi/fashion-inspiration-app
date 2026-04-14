"""
Garment classification via Groq Cloud (free).

Uses meta-llama/llama-4-scout-17b-16e-instruct — a vision-capable model
available on Groq's free tier.

Set GROQ_API_KEY in your .env file. Get/find yours at https://console.groq.com/keys
Falls back to a static mock result if no key is set (UI still works fully).
"""

import base64
import json
import os
from pathlib import Path

# ── Shared prompt ─────────────────────────────────────────────────────────────
_PROMPT = """Analyze this garment image and return ONLY a valid JSON object with these exact fields:

{
  "description": "2-3 sentence detailed description covering design details, construction, and overall aesthetic",
  "garment_type": "e.g. dress, jacket, blazer, coat, trousers, jeans, skirt, shirt, blouse, sweater, knitwear, jumpsuit, shorts, suit, vest, other",
  "style": "e.g. casual, formal, business casual, streetwear, bohemian, minimalist, maximalist, vintage, avant-garde, sporty, romantic, preppy, luxury, other",
  "material": "primary fabric (cotton, silk, denim, leather, linen, wool, cashmere, velvet, satin, knit, synthetic, etc.)",
  "color_palette": ["3 to 5 descriptive color names like 'navy blue', 'ivory', 'terracotta'"],
  "pattern": "solid, stripes, floral, geometric, abstract, animal print, plaid, paisley, tie-dye, color-block, embroidered, or other",
  "season": "spring/summer, fall/winter, or all-season",
  "occasion": "casual everyday, business casual, formal/black tie, evening/cocktail, outdoor/adventure, resort/vacation, athletic/activewear, or other",
  "consumer_profile": "concise target consumer description (e.g. 'young urban creative', 'luxury fashion buyer')",
  "trend_notes": "relevant trend references (quiet luxury, Y2K revival, coastal grandmother, etc.) or null",
  "location_context": "likely geographic context based on visual cues, or null",
  "continent": "continent name if determinable, or null",
  "country": "country name if determinable, or null",
  "city": "city name if determinable, or null",
  "year": null,
  "month": null,
  "confidence": {
    "garment_type": "high|medium|low",
    "style": "high|medium|low",
    "material": "high|medium|low",
    "color_palette": "high|medium|low",
    "pattern": "high|medium|low",
    "season": "high|medium|low",
    "occasion": "high|medium|low",
    "consumer_profile": "high|medium|low",
    "trend_notes": "high|medium|low",
    "continent": "high|medium|low",
    "country": "high|medium|low",
    "city": "high|medium|low"
  }
}

Return ONLY the JSON object. No markdown fences, no explanation."""

# ── Mock result (no API key configured) ──────────────────────────────────────
MOCK_RESULT: dict = {
    "description": (
        "A structured single-button blazer in a warm camel tone with a notched lapel "
        "and clean-cut silhouette. The fabric appears to be a medium-weight wool blend "
        "with a subtle texture, striking a balance between polish and approachability. "
        "Works equally well over trousers or thrown on top of straight-leg jeans."
    ),
    "garment_type": "blazer",
    "style": "business casual",
    "material": "wool blend",
    "color_palette": ["camel", "warm beige", "ivory"],
    "pattern": "solid",
    "season": "fall/winter",
    "occasion": "business casual",
    "consumer_profile": "young urban professional",
    "trend_notes": "quiet luxury",
    "location_context": "Western European boutique",
    "continent": "Europe",
    "country": None,
    "city": None,
    "year": None,
    "month": None,
    "confidence": {
        "garment_type": "high",
        "style": "high",
        "material": "medium",
        "color_palette": "high",
        "pattern": "high",
        "season": "high",
        "occasion": "high",
        "consumer_profile": "medium",
        "trend_notes": "medium",
        "continent": "medium",
        "country": "low",
        "city": "low",
    },
}


# ── Parser (shared) ───────────────────────────────────────────────────────────

def parse_model_output(raw: str) -> dict:
    """
    Parse and lightly validate the model's JSON response.
    Strips markdown code fences if the model adds them anyway.
    Raises json.JSONDecodeError on truly malformed output.
    """
    text = raw.strip()

    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].rstrip()

    data = json.loads(text)

    if not isinstance(data.get("color_palette"), list):
        data["color_palette"] = []
    if not isinstance(data.get("confidence"), dict):
        data["confidence"] = {}

    for field in ("trend_notes", "location_context", "continent", "country", "city", "year", "month"):
        if field not in data:
            data[field] = None

    return data


# ── Groq backend ──────────────────────────────────────────────────────────────

def _classify_groq(image_path: str) -> dict:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    suffix = Path(image_path).suffix.lower()
    mime_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif",
    }.get(suffix, "image/jpeg")

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
            },
            {"type": "text", "text": _PROMPT},
        ],
    }]

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        max_tokens=1024,
    )
    raw = response.choices[0].message.content

    try:
        return parse_model_output(raw)
    except (json.JSONDecodeError, ValueError):
        # One retry
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": "Your response was not valid JSON. Return only the JSON object, no markdown.",
        })
        retry = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            max_tokens=1024,
        )
        return parse_model_output(retry.choices[0].message.content)


# ── Public entry point ────────────────────────────────────────────────────────

def classify_image(image_path: str) -> dict:
    """
    Classify a garment image using Groq Cloud.
    Falls back to a static mock if GROQ_API_KEY is not set.
    """
    if os.getenv("GROQ_API_KEY"):
        return _classify_groq(image_path)
    return MOCK_RESULT.copy()
