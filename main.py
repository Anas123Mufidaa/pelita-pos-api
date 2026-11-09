from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from database import initialize_database
from exceptions import configure_error_handling
from models import ErrorResponse, SuccessResponse
from responses import build_response_meta
from routes.resource import router as resource_router


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
configure_error_handling(app)
app.include_router(resource_router)


@app.get(
    "/health",
    tags=["System"],
    summary="Periksa status API",
    description="Mengembalikan status sederhana untuk memastikan API berjalan.",
    response_model=SuccessResponse[dict[str, str]],
    response_model_exclude_none=True,
    responses={500: {"model": ErrorResponse, "description": "Internal server error"}},
)
async def health(request: Request) -> SuccessResponse[dict[str, str]]:
    return SuccessResponse(
        message="API is healthy",
        data={"status": "ok"},
        meta=build_response_meta(request),
    )
