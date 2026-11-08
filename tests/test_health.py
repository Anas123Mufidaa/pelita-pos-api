from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "API is healthy"
    assert body["data"] == {"status": "ok"}
    assert body["meta"]["request_id"].startswith("req_")
    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    datetime.fromisoformat(body["meta"]["timestamp"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_not_found_uses_standard_error_response() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/missing")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"] == {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Not Found",
    }
    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]


def test_openapi_documents_success_and_error_responses() -> None:
    responses = app.openapi()["paths"]["/health"]["get"]["responses"]

    assert "200" in responses
    assert "500" in responses
