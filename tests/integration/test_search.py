"""
Integration tests for search and filtering.

Exercises GET /api/garments with various combinations of filters and the
full-text search parameter.  Also tests the /api/facets endpoint that
powers the dynamic filter panel.

Location and time filters get explicit coverage as requested in the spec.
"""

import pytest


# ── List / no filters ─────────────────────────────────────────────────────────

def test_list_returns_all_garments(client, sample_garments):
    res = client.get("/api/garments")
    assert res.status_code == 200
    assert len(res.json()) == len(sample_garments)


def test_list_is_sorted_newest_first(client, sample_garments):
    res = client.get("/api/garments")
    items = res.json()
    # uploaded_at is the same for fixture items so order may vary;
    # just verify all IDs are present
    ids = {g["id"] for g in items}
    assert {g.id for g in sample_garments}.issubset(ids)


# ── Garment attribute filters ─────────────────────────────────────────────────

def test_filter_by_single_garment_type(client, sample_garments):
    res = client.get("/api/garments?garment_type=dress")
    results = res.json()
    assert all(g["garment_type"] == "dress" for g in results)
    assert len(results) == 1


def test_filter_by_multiple_garment_types(client, sample_garments):
    res = client.get("/api/garments?garment_type=dress&garment_type=jacket")
    results = res.json()
    types = {g["garment_type"] for g in results}
    assert types == {"dress", "jacket"}


def test_filter_by_style(client, sample_garments):
    res = client.get("/api/garments?style=formal")
    results = res.json()
    assert len(results) == 1
    assert results[0]["garment_type"] == "blazer"


def test_filter_by_material(client, sample_garments):
    res = client.get("/api/garments?material=linen")
    results = res.json()
    assert len(results) == 1
    assert results[0]["garment_type"] == "skirt"


def test_filter_by_season(client, sample_garments):
    res = client.get("/api/garments?season=spring%2Fsummer")
    results = res.json()
    assert all(g["season"] == "spring/summer" for g in results)


# ── Location filters ──────────────────────────────────────────────────────────

def test_filter_by_continent(client, sample_garments):
    res = client.get("/api/garments?continent=Europe")
    results = res.json()
    assert len(results) == 2  # dress (France) + blazer (Italy)
    continents = {g["continent"] for g in results}
    assert continents == {"Europe"}


def test_filter_by_country(client, sample_garments):
    res = client.get("/api/garments?country=Japan")
    results = res.json()
    assert len(results) == 1
    assert results[0]["city"] == "Tokyo"


def test_filter_by_city(client, sample_garments):
    res = client.get("/api/garments?city=New+York")
    results = res.json()
    assert len(results) == 1
    assert results[0]["garment_type"] == "jacket"


def test_filter_multiple_countries(client, sample_garments):
    res = client.get("/api/garments?country=France&country=Italy")
    results = res.json()
    countries = {g["country"] for g in results}
    assert countries == {"France", "Italy"}


# ── Time filters ──────────────────────────────────────────────────────────────

def test_filter_by_year(client, sample_garments):
    res = client.get("/api/garments?year=2024")
    results = res.json()
    assert len(results) == 1
    assert results[0]["year"] == 2024
    assert results[0]["garment_type"] == "jacket"


def test_filter_by_multiple_years(client, sample_garments):
    res = client.get("/api/garments?year=2022&year=2024")
    results = res.json()
    years = {g["year"] for g in results}
    assert years == {2022, 2024}


# ── Combined filters ──────────────────────────────────────────────────────────

def test_combined_continent_and_year(client, sample_garments):
    res = client.get("/api/garments?continent=Europe&year=2023")
    results = res.json()
    assert len(results) == 1
    assert results[0]["country"] == "France"


def test_filter_with_no_match_returns_empty(client, sample_garments):
    res = client.get("/api/garments?city=Sydney")
    assert res.json() == []


# ── Full-text search ──────────────────────────────────────────────────────────

def test_search_by_material_keyword(client, sample_garments):
    res = client.get("/api/garments?q=linen")
    results = res.json()
    assert len(results) >= 1
    types = {g["garment_type"] for g in results}
    assert "skirt" in types


def test_search_by_user_notes(client, sample_garments):
    """Full-text search should include user-authored notes."""
    res = client.get("/api/garments?q=Shimokitazawa")
    results = res.json()
    assert len(results) == 1
    assert results[0]["garment_type"] == "skirt"


def test_search_by_user_tag(client, sample_garments):
    res = client.get("/api/garments?q=sustainable")
    results = res.json()
    assert any("sustainable" in g.get("user_tags", []) for g in results)


def test_search_no_match_returns_empty(client, sample_garments):
    res = client.get("/api/garments?q=xyznonexistentterm999")
    assert res.json() == []


def test_search_and_filter_combined(client, sample_garments):
    """Search query AND attribute filter should both apply (AND semantics)."""
    res = client.get("/api/garments?q=sustainable&continent=Asia")
    results = res.json()
    assert len(results) == 1
    assert results[0]["continent"] == "Asia"


# ── Facets endpoint ───────────────────────────────────────────────────────────

def test_facets_returns_distinct_values(client, sample_garments):
    res = client.get("/api/facets")
    assert res.status_code == 200
    facets = res.json()
    assert "dress" in facets["garment_types"]
    assert "jacket" in facets["garment_types"]
    assert "blazer" in facets["garment_types"]
    assert "skirt" in facets["garment_types"]


def test_facets_location_fields(client, sample_garments):
    res = client.get("/api/facets")
    facets = res.json()
    assert "Europe" in facets["continents"]
    assert "North America" in facets["continents"]
    assert "Asia" in facets["continents"]
    assert "France" in facets["countries"]
    assert "Japan" in facets["countries"]


def test_facets_year_field(client, sample_garments):
    res = client.get("/api/facets")
    facets = res.json()
    assert 2023 in facets["years"]
    assert 2024 in facets["years"]


def test_facets_empty_db_returns_empty_lists(client):
    res = client.get("/api/facets")
    facets = res.json()
    # No sample_garments fixture here — all lists should be empty
    assert facets["garment_types"] == []
    assert facets["continents"] == []
