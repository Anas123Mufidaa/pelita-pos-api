import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite


DATABASE_PATH = Path(os.getenv("PELITA_DATABASE_PATH", "pelita_pos.db"))

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE CHECK (length(trim(sku)) > 0),
    nama TEXT NOT NULL CHECK (length(trim(nama)) > 0),
    kategori TEXT NOT NULL CHECK (length(trim(kategori)) > 0),
    harga INTEGER NOT NULL CHECK (harga >= 0),
    stok INTEGER NOT NULL CHECK (stok >= 0)
)
"""


@asynccontextmanager
async def connect_database(
    database_path: str | Path = DATABASE_PATH,
) -> AsyncIterator[aiosqlite.Connection]:
    async with aiosqlite.connect(database_path) as connection:
        connection.row_factory = aiosqlite.Row
        await connection.execute("PRAGMA foreign_keys = ON")
        yield connection


async def initialize_database(database_path: str | Path = DATABASE_PATH) -> None:
    async with connect_database(database_path) as connection:
        await connection.execute(CREATE_PRODUCTS_TABLE)
        await connection.commit()


def get_database_path() -> Path:
    return DATABASE_PATH


async def fetch_products(
    *,
    skip: int,
    limit: int,
    database_path: str | Path = DATABASE_PATH,
) -> tuple[list[aiosqlite.Row], int]:
    async with connect_database(database_path) as connection:
        count_cursor = await connection.execute("SELECT COUNT(*) FROM products")
        total = (await count_cursor.fetchone())[0]
        cursor = await connection.execute(
            """
            SELECT id, sku, nama, kategori, harga, stok
            FROM products
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (limit, skip),
        )
        return await cursor.fetchall(), total


async def fetch_product(
    product_id: int,
    *,
    database_path: str | Path = DATABASE_PATH,
) -> aiosqlite.Row | None:
    async with connect_database(database_path) as connection:
        cursor = await connection.execute(
            """
            SELECT id, sku, nama, kategori, harga, stok
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        )
        return await cursor.fetchone()
