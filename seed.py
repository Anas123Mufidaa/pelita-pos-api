import asyncio
from pathlib import Path

from database import DATABASE_PATH, connect_database, initialize_database


PRODUCTS = [
    ("KOPI-001", "Americano", "Minuman", 18000, 50),
    ("KOPI-002", "Cappuccino", "Minuman", 22000, 40),
    ("KOPI-003", "Kopi Susu Gula Aren", "Minuman", 23000, 45),
    ("TEH-001", "Teh Manis", "Minuman", 10000, 60),
    ("TEH-002", "Lemon Tea", "Minuman", 15000, 35),
    ("MAKAN-001", "Roti Bakar Cokelat", "Makanan", 20000, 30),
    ("MAKAN-002", "Kentang Goreng", "Makanan", 18000, 25),
    ("MAKAN-003", "Nasi Goreng", "Makanan", 28000, 20),
    ("SNACK-001", "Pisang Goreng", "Camilan", 16000, 30),
    ("SNACK-002", "Singkong Keju", "Camilan", 17000, 25),
]


async def seed_products(database_path: str | Path = DATABASE_PATH) -> int:
    await initialize_database(database_path)
    async with connect_database(database_path) as connection:
        await connection.executemany(
            """
            INSERT OR IGNORE INTO products (sku, nama, kategori, harga, stok)
            VALUES (?, ?, ?, ?, ?)
            """,
            PRODUCTS,
        )
        await connection.commit()
        return connection.total_changes


async def main() -> None:
    inserted = await seed_products()
    print(f"Seed complete: {inserted} product(s) inserted.")


if __name__ == "__main__":
    asyncio.run(main())
