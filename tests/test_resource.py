from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from database import get_database_path
from main import app
from seed import seed_products


@asynccontextmanager
async def resource_client(tmp_path) -> AsyncIterator[AsyncClient]:
    database_path = tmp_path / "test.db"
    await seed_products(database_path)
    app.dependency_overrides[get_database_path] = lambda: database_path
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_database_path, None)


@pytest.mark.asyncio
async def test_list_products_returns_paginated_products(tmp_path) -> None:
    async with resource_client(tmp_path) as client:
        response = await client.get("/resource", params={"skip": 2, "limit": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 3
    assert body["data"][0]["id"] == 3
    assert body["meta"]["pagination"] == {
        "skip": 2,
        "limit": 3,
        "total": 10,
        "has_next": True,
    }


@pytest.mark.asyncio
async def test_list_products_rejects_invalid_pagination(tmp_path) -> None:
    async with resource_client(tmp_path) as client:
        response = await client.get("/resource", params={"limit": 101})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_get_product_returns_product_or_not_found(tmp_path) -> None:
    async with resource_client(tmp_path) as client:
        found = await client.get("/resource/1")
        missing = await client.get("/resource/999")

    assert found.status_code == 200
    assert found.json()["data"]["sku"] == "KOPI-001"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_product_persists_product(tmp_path) -> None:
    payload = {
        "sku": "JUS-001",
        "nama": "Jus Jeruk",
        "kategori": "Minuman",
        "harga": 16000,
        "stok": 15,
    }
    async with resource_client(tmp_path) as client:
        created = await client.post("/resource", json=payload)
        product_id = created.json()["data"]["id"]
        persisted = await client.get(f"/resource/{product_id}")

    assert created.status_code == 201
    assert created.headers["Location"] == f"/resource/{product_id}"
    assert created.json()["data"]["sku"] == "JUS-001"
    assert persisted.status_code == 200
    assert persisted.json()["data"] == created.json()["data"]


@pytest.mark.asyncio
async def test_create_product_rejects_duplicate_sku(tmp_path) -> None:
    payload = {
        "sku": "KOPI-001",
        "nama": "Produk Duplikat",
        "kategori": "Minuman",
        "harga": 10000,
        "stok": 1,
    }
    async with resource_client(tmp_path) as client:
        response = await client.post("/resource", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_RESOURCE"


@pytest.mark.asyncio
async def test_create_product_rejects_invalid_payload(tmp_path) -> None:
    payload = {
        "sku": "JUS-001",
        "nama": "Jus Jeruk",
        "kategori": "Minuman",
        "harga": -1,
        "stok": 15,
    }
    async with resource_client(tmp_path) as client:
        response = await client.post("/resource", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
