import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from database import (
    fetch_product,
    fetch_transaction,
    get_database_path,
    reserve_transaction,
)
from main import app
from models import TransactionCreate
from routes import transaction as transaction_routes
from seed import seed_products


@asynccontextmanager
async def transaction_client(
    tmp_path, monkeypatch
) -> AsyncIterator[tuple[AsyncClient, object]]:
    database_path = tmp_path / "test.db"
    await seed_products(database_path)
    app.dependency_overrides[get_database_path] = lambda: database_path
    monkeypatch.setattr(transaction_routes, "PROCESSING_DELAY_SECONDS", 0)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client, database_path
    finally:
        app.dependency_overrides.pop(get_database_path, None)


@pytest.mark.asyncio
async def test_transaction_is_accepted_and_completed(tmp_path, monkeypatch) -> None:
    async with transaction_client(tmp_path, monkeypatch) as (client, database_path):
        response = await client.post(
            "/transactions",
            json={"product_id": 1, "quantity": 2, "cashier_name": "Kasir A"},
        )
        transaction_id = response.json()["data"]["id"]
        detail = await client.get(f"/transactions/{transaction_id}")
        product = await fetch_product(1, database_path=database_path)

    assert response.status_code == 202
    assert response.headers["Location"] == f"/transactions/{transaction_id}"
    assert response.json()["data"]["status"] == "pending"
    assert response.json()["data"]["unit_price"] == 18000
    assert response.json()["data"]["total_price"] == 36000
    assert detail.json()["data"]["status"] == "completed"
    assert product["stok"] == 48


@pytest.mark.asyncio
async def test_transaction_rejects_missing_product_and_stock(
    tmp_path, monkeypatch
) -> None:
    async with transaction_client(tmp_path, monkeypatch) as (client, _):
        missing = await client.post(
            "/transactions",
            json={"product_id": 999, "quantity": 1, "cashier_name": "Kasir"},
        )
        insufficient = await client.post(
            "/transactions",
            json={"product_id": 1, "quantity": 999, "cashier_name": "Kasir"},
        )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PRODUCT_NOT_FOUND"
    assert insufficient.status_code == 409
    assert insufficient.json()["error"]["code"] == "INSUFFICIENT_STOCK"


@pytest.mark.asyncio
async def test_transaction_list_filters_status(tmp_path, monkeypatch) -> None:
    async with transaction_client(tmp_path, monkeypatch) as (client, _):
        await client.post(
            "/transactions",
            json={"product_id": 1, "quantity": 1, "cashier_name": "Kasir"},
        )
        completed = await client.get("/transactions", params={"status": "completed"})
        pending = await client.get("/transactions", params={"status": "pending"})

    assert completed.status_code == 200
    assert completed.json()["meta"]["pagination"]["total"] == 1
    assert pending.json()["meta"]["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_safe_concurrent_transactions_allow_only_one(
    tmp_path, monkeypatch
) -> None:
    async with transaction_client(tmp_path, monkeypatch) as (client, _):
        product = (await client.get("/resource/1")).json()["data"]
        product["stok"] = 1
        product.pop("id")
        await client.put("/resource/1", json=product)
        payload = {"product_id": 1, "quantity": 1, "cashier_name": "Kasir"}
        first, second = await asyncio.gather(
            client.post("/transactions", json=payload),
            client.post("/transactions", json=payload),
        )

    assert sorted([first.status_code, second.status_code]) == [202, 409]


@pytest.mark.asyncio
async def test_background_failure_marks_transaction_failed(
    tmp_path, monkeypatch
) -> None:
    database_path = tmp_path / "test.db"
    await seed_products(database_path)
    transaction = TransactionCreate(product_id=1, quantity=1, cashier_name="Kasir")
    row = await reserve_transaction(transaction, database_path=database_path)

    async def fail_sleep(_: float) -> None:
        raise RuntimeError("simulated background failure")

    monkeypatch.setattr(transaction_routes.asyncio, "sleep", fail_sleep)
    await transaction_routes.process_transaction(row["id"], database_path)
    failed = await fetch_transaction(row["id"], database_path=database_path)

    assert failed["status"] == "failed"
