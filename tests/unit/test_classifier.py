"""
Unit tests for classifier.parse_model_output.

These tests verify that the parser handles valid JSON, markdown-wrapped
output, missing optional fields, and malformed responses correctly —
without making any real API calls.
"""

import json
import pytest
from app.services.classifier import parse_model_output


# ── Helpers ───────────────────────────────────────────────────────────────────

def minimal_valid_payload(**overrides):
    """Return a dict that satisfies the full schema."""
    base = {
        "description": "A crisp white cotton shirt with a spread collar.",
        "garment_type": "shirt",
        "style": "casual",
        "material": "cotton",
        "color_palette": ["white"],
        "pattern": "solid",
        "season": "all-season",
        "occasion": "casual everyday",
        "consumer_profile": "young professional",
        "trend_notes": None,
        "location_context": None,
        "continent": None,
        "country": None,
        "city": None,
        "year": None,
        "month": None,
        "confidence": {
            "garment_type": "high",
            "style": "high",
            "material": "high",
        },
    }
    base.update(overrides)
    return base


# ── Happy path ────────────────────────────────────────────────────────────────

def test_parse_valid_json():
    """Well-formed JSON string should round-trip cleanly."""
    payload = minimal_valid_payload()
    result = parse_model_output(json.dumps(payload))
    assert result["garment_type"] == "shirt"
    assert result["color_palette"] == ["white"]
    assert result["confidence"]["garment_type"] == "high"


def test_parse_strips_markdown_json_fence():
    """
    Claude sometimes wraps output in ```json ... ``` despite being told not to.
    The parser should handle this gracefully.
    """
    payload = minimal_valid_payload()
    wrapped = f"```json\n{json.dumps(payload)}\n```"
    result = parse_model_output(wrapped)
    assert result["garment_type"] == "shirt"


def test_parse_strips_plain_code_fence():
    """Also handles ``` without the language specifier."""
    payload = minimal_valid_payload()
    wrapped = f"```\n{json.dumps(payload)}\n```"
    result = parse_model_output(wrapped)
    assert result["material"] == "cotton"


def test_parse_strips_leading_trailing_whitespace():
    payload = minimal_valid_payload()
    result = parse_model_output("\n  " + json.dumps(payload) + "  \n")
    assert result["style"] == "casual"


# ── Optional field normalisation ──────────────────────────────────────────────

def test_missing_optional_location_fields_default_to_none():
    """continent/country/city are optional — omitting them should yield None."""
    payload = minimal_valid_payload()
    del payload["continent"]
    del payload["country"]
    del payload["city"]
    result = parse_model_output(json.dumps(payload))
    assert result["continent"] is None
    assert result["country"] is None
    assert result["city"] is None


def test_missing_trend_notes_defaults_to_none():
    payload = minimal_valid_payload()
    del payload["trend_notes"]
    result = parse_model_output(json.dumps(payload))
    assert result["trend_notes"] is None


def test_color_palette_not_list_becomes_empty_list():
    """If the model returns a string instead of a list, coerce to []."""
    payload = minimal_valid_payload(color_palette="navy blue")
    result = parse_model_output(json.dumps(payload))
    assert result["color_palette"] == []


def test_confidence_not_dict_becomes_empty_dict():
    payload = minimal_valid_payload(confidence="high")
    result = parse_model_output(json.dumps(payload))
    assert result["confidence"] == {}


# ── Error handling ────────────────────────────────────────────────────────────

def test_invalid_json_raises():
    """Truly broken JSON should surface a JSONDecodeError."""
    with pytest.raises(json.JSONDecodeError):
        parse_model_output("this is not json at all")


def test_empty_string_raises():
    with pytest.raises(json.JSONDecodeError):
        parse_model_output("")


def test_just_whitespace_raises():
    with pytest.raises(json.JSONDecodeError):
        parse_model_output("   \n  ")


# ── Realistic edge cases ──────────────────────────────────────────────────────

def test_multiword_color_names_preserved():
    """Color names like 'navy blue' or 'dusty rose' should pass through unchanged."""
    payload = minimal_valid_payload(color_palette=["navy blue", "dusty rose", "ivory"])
    result = parse_model_output(json.dumps(payload))
    assert "navy blue" in result["color_palette"]
    assert "dusty rose" in result["color_palette"]


def test_year_and_month_can_be_none():
    payload = minimal_valid_payload(year=None, month=None)
    result = parse_model_output(json.dumps(payload))
    assert result["year"] is None
    assert result["month"] is None


def test_year_and_month_integers_preserved():
    payload = minimal_valid_payload(year=2024, month=6)
    result = parse_model_output(json.dumps(payload))
    assert result["year"] == 2024
    assert result["month"] == 6
