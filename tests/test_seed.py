import pytest

from database import connect_database
from seed import PRODUCTS, seed_products


@pytest.mark.asyncio
async def test_seed_products_inserts_ten_products_once(tmp_path) -> None:
    database_path = tmp_path / "test.db"

    first_insert = await seed_products(database_path)
    second_insert = await seed_products(database_path)

    async with connect_database(database_path) as connection:
        cursor = await connection.execute("SELECT COUNT(*) FROM products")
        product_count = (await cursor.fetchone())[0]

    assert len(PRODUCTS) == 10
    assert first_insert == 10
    assert second_insert == 0
    assert product_count == 10
