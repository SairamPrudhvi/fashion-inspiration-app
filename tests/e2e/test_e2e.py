"""
End-to-end test: Upload → Classify → List → Filter → Annotate → Search annotation.

This test drives the full application workflow through the HTTP API,
mimicking what a designer would do in the browser.  The Claude classifier
is mocked so the test is deterministic and doesn't need an API key.

Note: A true browser-level E2E test (with Playwright or Selenium) would give
more confidence that the frontend JS is wired up correctly.  That layer is
noted as a future improvement in the README.  These tests cover the complete
backend contract end-to-end.
"""

import io
import pytest


# ── Full workflow ─────────────────────────────────────────────────────────────

def test_upload_classify_filter_workflow(client, minimal_image_bytes):
    """
    Covers the primary user journey:
      1. Upload three images (batch) from different locations
      2. Verify all appear in the gallery
      3. Apply a location filter — only the matching image appears
      4. Apply a year filter — narrows further
      5. Search by text — finds the right item
    """
    from unittest.mock import patch
    from tests.conftest import MOCK_CLASSIFICATION
    import copy

    paris_result   = copy.deepcopy(MOCK_CLASSIFICATION)
    tokyo_result   = {**copy.deepcopy(MOCK_CLASSIFICATION), "continent": "Asia",
                      "country": "Japan", "city": "Tokyo", "garment_type": "skirt",
                      "style": "bohemian", "year": 2022}
    newyork_result = {**copy.deepcopy(MOCK_CLASSIFICATION), "continent": "North America",
                      "country": "USA", "city": "New York", "garment_type": "jacket",
                      "style": "streetwear", "year": 2024}

    upload_sequence = [paris_result, tokyo_result, newyork_result]
    call_count = {"n": 0}

    def sequential_classify(path):
        result = upload_sequence[call_count["n"] % len(upload_sequence)]
        call_count["n"] += 1
        return result

    with patch("app.services.classifier.classify_image", side_effect=sequential_classify):
        files = [
            ("files", ("paris.jpg",    io.BytesIO(minimal_image_bytes), "image/jpeg")),
            ("files", ("tokyo.jpg",    io.BytesIO(minimal_image_bytes), "image/jpeg")),
            ("files", ("newyork.jpg",  io.BytesIO(minimal_image_bytes), "image/jpeg")),
        ]
        upload_res = client.post("/api/garments/upload", files=files, data={"designer": "Riya"})

    assert upload_res.status_code == 200
    uploaded = upload_res.json()
    assert len(uploaded) == 3

    # Step 2: all garments visible in unfiltered list
    list_res = client.get("/api/garments")
    assert len(list_res.json()) == 3

    # Step 3: filter by continent
    europe_res = client.get("/api/garments?continent=Europe")
    assert len(europe_res.json()) == 1
    assert europe_res.json()[0]["city"] == "Paris"

    asia_res = client.get("/api/garments?continent=Asia")
    assert len(asia_res.json()) == 1
    assert asia_res.json()[0]["city"] == "Tokyo"

    # Step 4: filter by year
    year_res = client.get("/api/garments?year=2024")
    assert len(year_res.json()) == 1
    assert year_res.json()[0]["city"] == "New York"

    # Step 5: combined continent + style filter
    combo_res = client.get("/api/garments?continent=Asia&style=bohemian")
    assert len(combo_res.json()) == 1
    assert combo_res.json()[0]["garment_type"] == "skirt"


def test_annotate_and_search_workflow(client, minimal_image_bytes):
    """
    1. Upload an image
    2. Add a specific annotation note
    3. Verify the note is findable via full-text search
    4. Verify the AI fields are unchanged
    """
    upload_res = client.post(
        "/api/garments/upload",
        files=[("files", ("item.jpg", io.BytesIO(minimal_image_bytes), "image/jpeg"))],
    )
    garment_id = upload_res.json()[0]["id"]
    original_garment_type = upload_res.json()[0]["garment_type"]

    # Annotate with something unique
    annotate_res = client.patch(
        f"/api/garments/{garment_id}/annotations",
        json={
            "user_tags": ["vintage", "archive-worthy"],
            "user_notes": "Found this at the Portobello Road market, incredible texture.",
        },
    )
    assert annotate_res.status_code == 200

    # Search should find it by note content
    search_res = client.get("/api/garments?q=Portobello")
    found_ids = [g["id"] for g in search_res.json()]
    assert garment_id in found_ids

    # Search by tag
    tag_res = client.get("/api/garments?q=archive-worthy")
    assert garment_id in [g["id"] for g in tag_res.json()]

    # AI fields should be unchanged
    final = client.get(f"/api/garments/{garment_id}").json()
    assert final["garment_type"] == original_garment_type
    assert "Portobello" in final["user_notes"]


def test_similar_images_workflow(client, minimal_image_bytes):
    """
    Upload multiple garments with the same type+style, then verify
    the /similar endpoint returns the right neighbours.
    """
    from unittest.mock import patch
    from tests.conftest import MOCK_CLASSIFICATION
    import copy

    # All three are blazer / business casual (same as MOCK_CLASSIFICATION)
    with patch("app.services.classifier.classify_image", return_value=copy.deepcopy(MOCK_CLASSIFICATION)):
        files = [
            ("files", (f"blazer{i}.jpg", io.BytesIO(minimal_image_bytes), "image/jpeg"))
            for i in range(3)
        ]
        res = client.post("/api/garments/upload", files=files)

    ids = [g["id"] for g in res.json()]
    assert len(ids) == 3

    # Ask for similar images of the first one — should return the other two
    similar_res = client.get(f"/api/garments/{ids[0]}/similar")
    similar_ids = {g["id"] for g in similar_res.json()}
    assert ids[1] in similar_ids or ids[2] in similar_ids


def test_delete_removes_from_gallery(client, minimal_image_bytes):
    """Deleted garments should not appear in subsequent list calls."""
    upload_res = client.post(
        "/api/garments/upload",
        files=[("files", ("to_delete.jpg", io.BytesIO(minimal_image_bytes), "image/jpeg"))],
    )
    garment_id = upload_res.json()[0]["id"]

    # Confirm it's there
    assert any(g["id"] == garment_id for g in client.get("/api/garments").json())

    # Delete it
    del_res = client.delete(f"/api/garments/{garment_id}")
    assert del_res.status_code == 200

    # Confirm it's gone
    assert not any(g["id"] == garment_id for g in client.get("/api/garments").json())
    assert client.get(f"/api/garments/{garment_id}").status_code == 404
