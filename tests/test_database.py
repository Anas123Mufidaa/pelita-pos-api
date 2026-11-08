import sqlite3

import pytest

from database import connect_database, initialize_database


@pytest.mark.asyncio
async def test_initialize_database_creates_products_table(tmp_path) -> None:
    database_path = tmp_path / "test.db"

    await initialize_database(database_path)
    await initialize_database(database_path)

    async with connect_database(database_path) as connection:
        cursor = await connection.execute("PRAGMA table_info(products)")
        columns = {row[1] for row in await cursor.fetchall()}

    assert columns == {"id", "sku", "nama", "kategori", "harga", "stok"}


@pytest.mark.asyncio
async def test_products_table_enforces_data_integrity(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    await initialize_database(database_path)

    async with connect_database(database_path) as connection:
        await connection.execute(
            """
            INSERT INTO products (sku, nama, kategori, harga, stok)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("KOPI-001", "Kopi Susu", "Minuman", 18000, 10),
        )
        await connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            await connection.execute(
                """
                INSERT INTO products (sku, nama, kategori, harga, stok)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("KOPI-001", "Kopi Hitam", "Minuman", 12000, 5),
            )

        with pytest.raises(sqlite3.IntegrityError):
            await connection.execute(
                """
                INSERT INTO products (sku, nama, kategori, harga, stok)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("ROTI-001", "Roti Bakar", "Makanan", 15000, -1),
            )
