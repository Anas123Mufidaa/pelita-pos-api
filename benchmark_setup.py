import asyncio

from database import connect_database, initialize_database
from seed import seed_products


async def reset_benchmark_data() -> None:
    await initialize_database()
    await seed_products()
    async with connect_database() as connection:
        await connection.execute("DELETE FROM transactions")
        await connection.execute("UPDATE products SET stok = 10000 WHERE id = 1")
        await connection.commit()


if __name__ == "__main__":
    asyncio.run(reset_benchmark_data())
    print("Benchmark data reset: product 1 stock = 10000, transactions cleared.")
