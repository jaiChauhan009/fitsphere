"""Health, root, and OpenAPI endpoint tests."""
import pytest
from httpx import AsyncClient, ASGITransport
import main as app_module


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app), base_url="http://test"
    ) as ac:
        r = await ac.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["app"] == "FitSphere API"
    assert body["status"] == "running"


@pytest.mark.asyncio
async def test_health_endpoint(client):
    r = await client.get("/health")
    # DB may or may not connect, but endpoint must always respond
    assert r.status_code in (200, 503)
    body = r.json()
    assert "status" in body
    assert "api" in body
    assert "database" in body
    assert "latency_ms" in body


@pytest.mark.asyncio
async def test_openapi_schema():
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app), base_url="http://test"
    ) as ac:
        r = await ac.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert schema["info"]["title"] == "FitSphere API"
    paths = schema.get("paths", {})
    assert len(paths) > 10, "Expected many registered routes"
    # Check all major tag groups are present
    tags_found = set()
    for path_data in paths.values():
        for method_data in path_data.values():
            tags_found.update(method_data.get("tags", []))
    for expected_tag in ("users", "food", "nutrition", "workouts", "progress", "knowledge"):
        assert expected_tag in tags_found, f"Tag '{expected_tag}' missing from OpenAPI schema"


@pytest.mark.asyncio
async def test_no_auth_returns_401():
    """Endpoints that require auth must reject requests with no token (no overrides)."""
    from database import get_db
    from utils.firebase import get_current_firebase_uid

    # Build a clean app copy with no dependency overrides
    app = app_module.app
    saved = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            r = await ac.get("/users/me")
        assert r.status_code in (401, 403), f"Expected 401/403 without auth, got {r.status_code}"
    finally:
        app.dependency_overrides.update(saved)
