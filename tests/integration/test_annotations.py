"""
Integration tests for designer annotations.

Verifies that user_tags and user_notes can be added, updated, and searched,
and that they remain clearly separated from AI-generated fields.
"""

import io
import pytest


def create_garment(client, minimal_image_bytes):
    res = client.post(
        "/api/garments/upload",
        files=[("files", ("test.jpg", io.BytesIO(minimal_image_bytes), "image/jpeg"))],
    )
    assert res.status_code == 200
    return res.json()[0]


# ── Adding annotations ────────────────────────────────────────────────────────

def test_add_tags_to_garment(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    res = client.patch(
        f"/api/garments/{g['id']}/annotations",
        json={"user_tags": ["sustainable", "handmade"]},
    )
    assert res.status_code == 200
    updated = res.json()
    assert "sustainable" in updated["user_tags"]
    assert "handmade" in updated["user_tags"]


def test_add_notes_to_garment(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    res = client.patch(
        f"/api/garments/{g['id']}/annotations",
        json={"user_notes": "Spotted at the Marais concept store, great drape."},
    )
    assert res.status_code == 200
    updated = res.json()
    assert "Marais" in updated["user_notes"]


def test_add_both_tags_and_notes(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    res = client.patch(
        f"/api/garments/{g['id']}/annotations",
        json={"user_tags": ["resort"], "user_notes": "Perfect for the Bali trip."},
    )
    updated = res.json()
    assert "resort" in updated["user_tags"]
    assert "Bali" in updated["user_notes"]


# ── Update behaviour ──────────────────────────────────────────────────────────

def test_update_tags_replaces_existing(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    client.patch(f"/api/garments/{g['id']}/annotations", json={"user_tags": ["old-tag"]})
    res = client.patch(f"/api/garments/{g['id']}/annotations", json={"user_tags": ["new-tag"]})
    assert res.json()["user_tags"] == ["new-tag"]


def test_clear_tags_with_empty_list(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    client.patch(f"/api/garments/{g['id']}/annotations", json={"user_tags": ["to-remove"]})
    res = client.patch(f"/api/garments/{g['id']}/annotations", json={"user_tags": []})
    assert res.json()["user_tags"] == []


def test_tags_with_whitespace_are_trimmed(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    res = client.patch(
        f"/api/garments/{g['id']}/annotations",
        json={"user_tags": ["  sustainable  ", " eco "]},
    )
    tags = res.json()["user_tags"]
    assert "sustainable" in tags
    assert "eco" in tags
    assert "  sustainable  " not in tags


def test_empty_tags_are_filtered_out(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    res = client.patch(
        f"/api/garments/{g['id']}/annotations",
        json={"user_tags": ["valid", "", "  "]},
    )
    assert res.json()["user_tags"] == ["valid"]


# ── AI fields are not affected by annotation updates ─────────────────────────

def test_ai_fields_unchanged_after_annotation(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    original_type = g["garment_type"]
    original_desc = g["description"]
    client.patch(
        f"/api/garments/{g['id']}/annotations",
        json={"user_tags": ["test"], "user_notes": "Some notes"},
    )
    updated = client.get(f"/api/garments/{g['id']}").json()
    assert updated["garment_type"] == original_type
    assert updated["description"] == original_desc


# ── Annotations are searchable ────────────────────────────────────────────────

def test_user_notes_appear_in_search(client, minimal_image_bytes, db):
    g = create_garment(client, minimal_image_bytes)
    client.patch(
        f"/api/garments/{g['id']}/annotations",
        json={"user_notes": "Embroidered neckline from artisan market"},
    )
    res = client.get("/api/garments?q=artisan+market")
    ids = [item["id"] for item in res.json()]
    assert g["id"] in ids


def test_user_tags_appear_in_search(client, minimal_image_bytes):
    g = create_garment(client, minimal_image_bytes)
    client.patch(
        f"/api/garments/{g['id']}/annotations",
        json={"user_tags": ["embroidered", "handwoven"]},
    )
    res = client.get("/api/garments?q=handwoven")
    ids = [item["id"] for item in res.json()]
    assert g["id"] in ids


# ── Error handling ────────────────────────────────────────────────────────────

def test_annotate_nonexistent_garment_returns_404(client):
    res = client.patch(
        "/api/garments/does-not-exist/annotations",
        json={"user_notes": "test"},
    )
    assert res.status_code == 404
