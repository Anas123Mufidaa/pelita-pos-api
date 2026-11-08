from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await initialize_database()
    yield


tags_metadata = [
    {
        "name": "System",
        "description": "Pemeriksaan status Pelita POS API.",
    },
    {
        "name": "Dashboard",
        "description": "Pengelolaan produk dan pemantauan transaksi.",
    },
    {
        "name": "Cashier",
        "description": "Operasi transaksi aplikasi kasir.",
    },
]

app = FastAPI(
    title="Pelita POS API",
    description="Backend POS untuk Cashier App dan Dashboard",
    version="0.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)


@app.get(
    "/health",
    tags=["System"],
    summary="Periksa status API",
    description="Mengembalikan status sederhana untuk memastikan API berjalan.",
    response_model=dict[str, str],
)
async def health() -> dict[str, str]:
    return {"status": "ok"}
