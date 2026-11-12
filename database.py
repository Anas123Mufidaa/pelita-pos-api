import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from models import ProductCreate, ProductUpdate, TransactionCreate, TransactionStatus


class ProductNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


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

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    total_price INTEGER NOT NULL CHECK (total_price >= 0),
    cashier_name TEXT NOT NULL CHECK (length(trim(cashier_name)) > 0),
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'processing', 'completed', 'failed')
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        await connection.execute(CREATE_TRANSACTIONS_TABLE)
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


async def insert_product(
    product: ProductCreate,
    *,
    database_path: str | Path = DATABASE_PATH,
) -> aiosqlite.Row:
    async with connect_database(database_path) as connection:
        cursor = await connection.execute(
            """
            INSERT INTO products (sku, nama, kategori, harga, stok)
            VALUES (?, ?, ?, ?, ?)
            """,
            (product.sku, product.nama, product.kategori, product.harga, product.stok),
        )
        await connection.commit()
        created_cursor = await connection.execute(
            """
            SELECT id, sku, nama, kategori, harga, stok
            FROM products
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        )
        row = await created_cursor.fetchone()
        if row is None:
            raise RuntimeError("Created product could not be loaded")
        return row


async def update_product(
    product_id: int,
    product: ProductUpdate,
    *,
    database_path: str | Path = DATABASE_PATH,
) -> aiosqlite.Row | None:
    async with connect_database(database_path) as connection:
        cursor = await connection.execute(
            """
            UPDATE products
            SET sku = ?, nama = ?, kategori = ?, harga = ?, stok = ?
            WHERE id = ?
            """,
            (
                product.sku,
                product.nama,
                product.kategori,
                product.harga,
                product.stok,
                product_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
        await connection.commit()
        updated_cursor = await connection.execute(
            """
            SELECT id, sku, nama, kategori, harga, stok
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        )
        return await updated_cursor.fetchone()


async def delete_product(
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
        product = await cursor.fetchone()
        if product is None:
            return None
        await connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await connection.commit()
        return product


async def _insert_transaction(
    connection: aiosqlite.Connection,
    transaction: TransactionCreate,
    unit_price: int,
) -> aiosqlite.Row:
    cursor = await connection.execute(
        """
        INSERT INTO transactions (
            product_id, quantity, unit_price, total_price, cashier_name, status
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            transaction.product_id,
            transaction.quantity,
            unit_price,
            unit_price * transaction.quantity,
            transaction.cashier_name,
            TransactionStatus.PENDING.value,
        ),
    )
    created_cursor = await connection.execute(
        """
        SELECT id, product_id, quantity, unit_price, total_price,
               cashier_name, status, created_at
        FROM transactions WHERE id = ?
        """,
        (cursor.lastrowid,),
    )
    row = await created_cursor.fetchone()
    if row is None:
        raise RuntimeError("Created transaction could not be loaded")
    return row


async def reserve_transaction(
    transaction: TransactionCreate,
    *,
    database_path: str | Path = DATABASE_PATH,
) -> aiosqlite.Row:
    async with connect_database(database_path) as connection:
        try:
            # Lock before read/update so separate Uvicorn workers cannot oversell.
            await connection.execute("BEGIN IMMEDIATE")
            cursor = await connection.execute(
                "SELECT harga FROM products WHERE id = ?",
                (transaction.product_id,),
            )
            product = await cursor.fetchone()
            if product is None:
                raise ProductNotFoundError

            update = await connection.execute(
                """
                UPDATE products
                SET stok = stok - ?
                WHERE id = ? AND stok >= ?
                """,
                (
                    transaction.quantity,
                    transaction.product_id,
                    transaction.quantity,
                ),
            )
            if update.rowcount != 1:
                raise InsufficientStockError

            row = await _insert_transaction(connection, transaction, product["harga"])
            await connection.commit()
            return row
        except Exception:
            await connection.rollback()
            raise


async def reserve_transaction_unsafe(
    transaction: TransactionCreate,
    *,
    database_path: str | Path = DATABASE_PATH,
) -> aiosqlite.Row:
    async with connect_database(database_path) as connection:
        cursor = await connection.execute(
            "SELECT harga, stok FROM products WHERE id = ?",
            (transaction.product_id,),
        )
        product = await cursor.fetchone()
        if product is None:
            raise ProductNotFoundError

        current_stock = product["stok"]
        # Widen the read-modify-write window to reproduce the unsafe race on demand.
        await asyncio.sleep(0.01)
        if current_stock < transaction.quantity:
            raise InsufficientStockError

        await connection.execute(
            "UPDATE products SET stok = ? WHERE id = ?",
            (current_stock - transaction.quantity, transaction.product_id),
        )
        row = await _insert_transaction(connection, transaction, product["harga"])
        await connection.commit()
        return row


async def update_transaction_status(
    transaction_id: int,
    transaction_status: TransactionStatus,
    *,
    database_path: str | Path = DATABASE_PATH,
) -> None:
    async with connect_database(database_path) as connection:
        await connection.execute(
            "UPDATE transactions SET status = ? WHERE id = ?",
            (transaction_status.value, transaction_id),
        )
        await connection.commit()


async def fail_transaction_and_restore_stock(
    transaction_id: int,
    *,
    database_path: str | Path = DATABASE_PATH,
) -> None:
    async with connect_database(database_path) as connection:
        try:
            await connection.execute("BEGIN IMMEDIATE")
            cursor = await connection.execute(
                """
                SELECT product_id, quantity, status
                FROM transactions WHERE id = ?
                """,
                (transaction_id,),
            )
            transaction = await cursor.fetchone()
            if transaction is None or transaction["status"] not in (
                TransactionStatus.PENDING.value,
                TransactionStatus.PROCESSING.value,
            ):
                await connection.rollback()
                return
            await connection.execute(
                "UPDATE products SET stok = stok + ? WHERE id = ?",
                (transaction["quantity"], transaction["product_id"]),
            )
            await connection.execute(
                "UPDATE transactions SET status = ? WHERE id = ?",
                (TransactionStatus.FAILED.value, transaction_id),
            )
            await connection.commit()
        except Exception:
            await connection.rollback()
            raise


async def fetch_transaction(
    transaction_id: int,
    *,
    database_path: str | Path = DATABASE_PATH,
) -> aiosqlite.Row | None:
    async with connect_database(database_path) as connection:
        cursor = await connection.execute(
            """
            SELECT id, product_id, quantity, unit_price, total_price,
                   cashier_name, status, created_at
            FROM transactions WHERE id = ?
            """,
            (transaction_id,),
        )
        return await cursor.fetchone()


async def fetch_transactions(
    *,
    transaction_status: TransactionStatus | None,
    skip: int,
    limit: int,
    database_path: str | Path = DATABASE_PATH,
) -> tuple[list[aiosqlite.Row], int]:
    where = " WHERE status = ?" if transaction_status else ""
    parameters = (transaction_status.value,) if transaction_status else ()
    async with connect_database(database_path) as connection:
        count_cursor = await connection.execute(
            f"SELECT COUNT(*) FROM transactions{where}", parameters
        )
        total = (await count_cursor.fetchone())[0]
        cursor = await connection.execute(
            f"""
            SELECT id, product_id, quantity, unit_price, total_price,
                   cashier_name, status, created_at
            FROM transactions{where}
            ORDER BY id DESC LIMIT ? OFFSET ?
            """,
            (*parameters, limit, skip),
        )
        return await cursor.fetchall(), total
