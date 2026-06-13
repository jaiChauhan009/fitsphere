"""
Knowledge articles — list, get by ID, search, categories endpoint.
"""
import pytest


# ── GET /knowledge/articles ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_articles(client):
    r = await client.get("/knowledge/articles")
    assert r.status_code == 200, r.text
    articles = r.json()
    assert isinstance(articles, list)
    assert len(articles) >= 2  # seeded 2 articles


@pytest.mark.asyncio
async def test_list_articles_by_category(client):
    r = await client.get("/knowledge/articles", params={"category": "nutrition"})
    assert r.status_code == 200
    articles = r.json()
    assert len(articles) >= 1
    for a in articles:
        assert a["category"] == "nutrition"


@pytest.mark.asyncio
async def test_list_articles_by_query(client):
    """Full-text search on title/summary."""
    r = await client.get("/knowledge/articles", params={"q": "protein"})
    assert r.status_code == 200
    articles = r.json()
    assert len(articles) >= 1
    # At least one result should mention protein
    titles_and_summaries = " ".join(
        a.get("title", "") + " " + a.get("summary", "") for a in articles
    ).lower()
    assert "protein" in titles_and_summaries


@pytest.mark.asyncio
async def test_list_articles_by_category_recovery(client):
    r = await client.get("/knowledge/articles", params={"category": "recovery"})
    assert r.status_code == 200
    articles = r.json()
    assert len(articles) >= 1
    for a in articles:
        assert a["category"] == "recovery"


@pytest.mark.asyncio
async def test_list_articles_empty_category(client):
    r = await client.get("/knowledge/articles", params={"category": "nonexistent_xyz"})
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_articles_limit(client):
    r = await client.get("/knowledge/articles", params={"limit": 1})
    assert r.status_code == 200
    assert len(r.json()) <= 1


@pytest.mark.asyncio
async def test_list_articles_limit_exceeded(client):
    """limit > 100 must be rejected."""
    r = await client.get("/knowledge/articles", params={"limit": 101})
    assert r.status_code == 422


# ── GET /knowledge/articles/{id} ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_article_by_id(client):
    """Fetch a specific article using its ID from the list endpoint."""
    articles = (await client.get("/knowledge/articles")).json()
    article_id = articles[0]["id"]

    r = await client.get(f"/knowledge/articles/{article_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == article_id
    assert "title" in body
    assert "content" in body
    assert "category" in body


@pytest.mark.asyncio
async def test_get_article_not_found(client):
    r = await client.get("/knowledge/articles/nonexistent-article-id")
    assert r.status_code == 404


# ── GET /knowledge/categories ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_categories(client):
    r = await client.get("/knowledge/categories")
    assert r.status_code == 200, r.text
    categories = r.json()
    assert isinstance(categories, list)
    ids = [c["id"] for c in categories]
    for expected in ("nutrition", "workout", "recovery", "mental_health", "supplements"):
        assert expected in ids, f"Category '{expected}' missing"


@pytest.mark.asyncio
async def test_categories_have_labels(client):
    r = await client.get("/knowledge/categories")
    for cat in r.json():
        assert "id" in cat
        assert "label" in cat
        assert len(cat["label"]) > 0
