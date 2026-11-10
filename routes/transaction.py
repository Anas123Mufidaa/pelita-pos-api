import asyncio
import logging
import os
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    Request,
    Response,
    status,
)
from fastapi import Path as PathParameter

from database import (
    InsufficientStockError,
    ProductNotFoundError,
    fetch_transaction,
    fetch_transactions,
    get_database_path,
    reserve_transaction,
    reserve_transaction_unsafe,
    update_transaction_status,
)
from exceptions import AppException
from models import (
    ErrorCode,
    ErrorResponse,
    PaginationMeta,
    SuccessResponse,
    TransactionCreate,
    TransactionRead,
    TransactionStatus,
)
from responses import build_response_meta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["Cashier"])
stock_lock = asyncio.Lock()
PROCESSING_DELAY_SECONDS = 3


async def process_transaction(
    transaction_id: int,
    database_path: str | Path,
) -> None:
    try:
        await update_transaction_status(
            transaction_id,
            TransactionStatus.PROCESSING,
            database_path=database_path,
        )
        await asyncio.sleep(PROCESSING_DELAY_SECONDS)
        await update_transaction_status(
            transaction_id,
            TransactionStatus.COMPLETED,
            database_path=database_path,
        )
    except Exception:
        logger.exception(
            "Background transaction failed", extra={"transaction_id": transaction_id}
        )
        try:
            await update_transaction_status(
                transaction_id,
                TransactionStatus.FAILED,
                database_path=database_path,
            )
        except Exception:
            logger.exception("Could not mark transaction as failed")


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[TransactionRead],
    response_model_exclude_none=True,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
        409: {"model": ErrorResponse, "description": "Insufficient stock"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Create a pending transaction",
)
async def create_transaction(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    transaction: TransactionCreate,
    database_path: Annotated[Path, Depends(get_database_path)],
) -> SuccessResponse[TransactionRead]:
    try:
        if os.getenv("PELITA_UNSAFE_STOCK") == "1":
            row = await reserve_transaction_unsafe(
                transaction, database_path=database_path
            )
        else:
            async with stock_lock:
                row = await reserve_transaction(
                    transaction, database_path=database_path
                )
    except ProductNotFoundError as exception:
        raise AppException(
            status_code=404,
            code=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product not found",
        ) from exception
    except InsufficientStockError as exception:
        raise AppException(
            status_code=409,
            code=ErrorCode.INSUFFICIENT_STOCK,
            message="Insufficient product stock",
        ) from exception

    created = TransactionRead(**dict(row))
    background_tasks.add_task(process_transaction, created.id, database_path)
    response.headers["Location"] = f"/transactions/{created.id}"
    return SuccessResponse(
        message="Transaction accepted for processing",
        data=created,
        meta=build_response_meta(request),
    )


@router.get(
    "",
    response_model=SuccessResponse[list[TransactionRead]],
    response_model_exclude_none=True,
)
async def list_transactions(
    request: Request,
    database_path: Annotated[Path, Depends(get_database_path)],
    transaction_status: Annotated[
        TransactionStatus | None, Query(alias="status")
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> SuccessResponse[list[TransactionRead]]:
    rows, total = await fetch_transactions(
        transaction_status=transaction_status,
        skip=skip,
        limit=limit,
        database_path=database_path,
    )
    transactions = [TransactionRead(**dict(row)) for row in rows]
    pagination = PaginationMeta(
        skip=skip, limit=limit, total=total, has_next=skip + len(transactions) < total
    )
    return SuccessResponse(
        message="Transactions retrieved successfully",
        data=transactions,
        meta=build_response_meta(request, pagination),
    )


@router.get(
    "/{transaction_id}",
    response_model=SuccessResponse[TransactionRead],
    response_model_exclude_none=True,
)
async def get_transaction(
    request: Request,
    database_path: Annotated[Path, Depends(get_database_path)],
    transaction_id: Annotated[int, PathParameter(gt=0)],
) -> SuccessResponse[TransactionRead]:
    row = await fetch_transaction(transaction_id, database_path=database_path)
    if row is None:
        raise AppException(
            status_code=404,
            code=ErrorCode.TRANSACTION_NOT_FOUND,
            message="Transaction not found",
        )
    return SuccessResponse(
        message="Transaction retrieved successfully",
        data=TransactionRead(**dict(row)),
        meta=build_response_meta(request),
    )
