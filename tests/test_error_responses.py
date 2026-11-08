import pytest
from fastapi import FastAPI, Query
from httpx import ASGITransport, AsyncClient

from exceptions import configure_error_handling


def create_test_app() -> FastAPI:
    test_app = FastAPI()
    configure_error_handling(test_app)

    @test_app.get("/validate")
    async def validate(limit: int = Query(ge=1)) -> dict[str, int]:
        return {"limit": limit}

    @test_app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("internal database secret")

    return test_app


@pytest.mark.asyncio
async def test_validation_error_uses_standard_response() -> None:
    transport = ASGITransport(app=create_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/validate", params={"limit": 0})

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"][0]["field"] == "query.limit"


@pytest.mark.asyncio
async def test_internal_error_does_not_leak_details() -> None:
    transport = ASGITransport(app=create_test_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/crash")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert "database secret" not in response.text
