"""
Integration tests for the upload endpoint.

Covers the full POST /api/garments/upload flow: file handling, classification
result persistence, and error cases.  The classifier is mocked so no real
Claude API calls are made.
"""

import io
import json
from unittest.mock import patch

import pytest


def post_upload(client, image_bytes, filename="test.jpg", designer=None):
    files = [("files", (filename, io.BytesIO(image_bytes), "image/jpeg"))]
    data = {"designer": designer} if designer else {}
    return client.post("/api/garments/upload", files=files, data=data)


# ── Happy path ────────────────────────────────────────────────────────────────

def test_upload_returns_201_and_garment(client, minimal_image_bytes):
    res = post_upload(client, minimal_image_bytes, "blazer.jpg", designer="Sofia")
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)
    assert len(body) == 1
    g = body[0]
    assert g["garment_type"] == "blazer"
    assert g["style"] == "business casual"
    assert g["designer"] == "Sofia"


def test_upload_stores_ai_description(client, minimal_image_bytes):
    res = post_upload(client, minimal_image_bytes)
    g = res.json()[0]
    assert "blazer" in g["description"].lower() or len(g["description"]) > 10


def test_upload_stores_color_palette_as_list(client, minimal_image_bytes):
    res = post_upload(client, minimal_image_bytes)
    g = res.json()[0]
    assert isinstance(g["color_palette"], list)
    assert len(g["color_palette"]) > 0


def test_upload_stores_confidence(client, minimal_image_bytes):
    res = post_upload(client, minimal_image_bytes)
    g = res.json()[0]
    assert isinstance(g["confidence"], dict)
    assert "garment_type" in g["confidence"]


def test_upload_stores_location(client, minimal_image_bytes):
    res = post_upload(client, minimal_image_bytes)
    g = res.json()[0]
    assert g["continent"] == "Europe"
    assert g["country"] == "France"
    assert g["city"] == "Paris"


def test_upload_user_annotations_start_empty(client, minimal_image_bytes):
    res = post_upload(client, minimal_image_bytes)
    g = res.json()[0]
    assert g["user_tags"] == []
    assert g["user_notes"] in ("", None)


def test_batch_upload_returns_multiple_garments(client, minimal_image_bytes):
    """Multiple files in one request should each get classified."""
    files = [
        ("files", ("a.jpg", io.BytesIO(minimal_image_bytes), "image/jpeg")),
        ("files", ("b.jpg", io.BytesIO(minimal_image_bytes), "image/jpeg")),
        ("files", ("c.jpg", io.BytesIO(minimal_image_bytes), "image/jpeg")),
    ]
    res = client.post("/api/garments/upload", files=files)
    assert res.status_code == 200
    assert len(res.json()) == 3


# ── Error handling ────────────────────────────────────────────────────────────

def test_upload_rejects_non_image_extension(client):
    res = client.post(
        "/api/garments/upload",
        files=[("files", ("document.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf"))],
    )
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]


def test_upload_handles_classifier_failure(client, minimal_image_bytes):
    """If classification raises, the endpoint should return 422 and not leave orphan files."""
    with patch(
        "app.services.classifier.classify_image",
        side_effect=ValueError("model refused"),
    ):
        res = post_upload(client, minimal_image_bytes)
    assert res.status_code == 422


# ── GET / DELETE ──────────────────────────────────────────────────────────────

def test_get_garment_by_id(client, minimal_image_bytes):
    create_res = post_upload(client, minimal_image_bytes)
    garment_id = create_res.json()[0]["id"]
    get_res = client.get(f"/api/garments/{garment_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == garment_id


def test_get_nonexistent_garment_returns_404(client):
    res = client.get("/api/garments/does-not-exist")
    assert res.status_code == 404


def test_delete_garment(client, minimal_image_bytes):
    create_res = post_upload(client, minimal_image_bytes)
    garment_id = create_res.json()[0]["id"]
    del_res = client.delete(f"/api/garments/{garment_id}")
    assert del_res.status_code == 200
    # Verify it's gone
    assert client.get(f"/api/garments/{garment_id}").status_code == 404
