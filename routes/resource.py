import sqlite3
from pathlib import Path
from typing import Annotated, NoReturn

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    Response,
    status,
)
from fastapi import (
    Path as PathParameter,
)

from database import (
    delete_product as delete_product_record,
)
from database import (
    fetch_product,
    fetch_products,
    get_database_path,
    insert_product,
)
from database import (
    update_product as update_product_record,
)
from exceptions import AppException
from models import (
    ErrorCode,
    ErrorResponse,
    PaginationMeta,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    SuccessResponse,
)
from responses import build_response_meta

router = APIRouter(prefix="/resource", tags=["Dashboard"])

COMMON_ERROR_RESPONSES = {
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
}


def raise_product_integrity_error(exception: sqlite3.IntegrityError) -> NoReturn:
    if "products.sku" in str(exception):
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.DUPLICATE_RESOURCE,
            message="Product SKU already exists",
        ) from exception
    raise exception


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[ProductRead],
    response_model_exclude_none=True,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "SKU already exists",
        },
        **COMMON_ERROR_RESPONSES,
    },
    summary="Create a product",
)
async def create_product(
    request: Request,
    response: Response,
    product: ProductCreate,
    database_path: Annotated[Path, Depends(get_database_path)],
) -> SuccessResponse[ProductRead]:
    try:
        row = await insert_product(product, database_path=database_path)
    except sqlite3.IntegrityError as exception:
        raise_product_integrity_error(exception)

    created = ProductRead(**dict(row))
    response.headers["Location"] = f"/resource/{created.id}"
    return SuccessResponse(
        message="Product created successfully",
        data=created,
        meta=build_response_meta(request),
    )


@router.get(
    "",
    response_model=SuccessResponse[list[ProductRead]],
    response_model_exclude_none=True,
    responses=COMMON_ERROR_RESPONSES,
    summary="List products",
)
async def list_products(
    request: Request,
    database_path: Annotated[Path, Depends(get_database_path)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> SuccessResponse[list[ProductRead]]:
    rows, total = await fetch_products(
        skip=skip,
        limit=limit,
        database_path=database_path,
    )
    products = [ProductRead(**dict(row)) for row in rows]
    pagination = PaginationMeta(
        skip=skip,
        limit=limit,
        total=total,
        has_next=skip + len(products) < total,
    )
    return SuccessResponse(
        message="Products retrieved successfully",
        data=products,
        meta=build_response_meta(request, pagination),
    )


@router.get(
    "/{product_id}",
    response_model=SuccessResponse[ProductRead],
    response_model_exclude_none=True,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Product not found",
        },
        **COMMON_ERROR_RESPONSES,
    },
    summary="Get product details",
)
async def get_product(
    request: Request,
    database_path: Annotated[Path, Depends(get_database_path)],
    product_id: Annotated[int, PathParameter(gt=0)],
) -> SuccessResponse[ProductRead]:
    row = await fetch_product(product_id, database_path=database_path)
    if row is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product not found",
        )

    return SuccessResponse(
        message="Product retrieved successfully",
        data=ProductRead(**dict(row)),
        meta=build_response_meta(request),
    )


@router.put(
    "/{product_id}",
    response_model=SuccessResponse[ProductRead],
    response_model_exclude_none=True,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Product not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "SKU already exists",
        },
        **COMMON_ERROR_RESPONSES,
    },
    summary="Update a product",
)
async def update_product(
    request: Request,
    product: ProductUpdate,
    database_path: Annotated[Path, Depends(get_database_path)],
    product_id: Annotated[int, PathParameter(gt=0)],
) -> SuccessResponse[ProductRead]:
    try:
        row = await update_product_record(
            product_id,
            product,
            database_path=database_path,
        )
    except sqlite3.IntegrityError as exception:
        raise_product_integrity_error(exception)

    if row is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product not found",
        )

    return SuccessResponse(
        message="Product updated successfully",
        data=ProductRead(**dict(row)),
        meta=build_response_meta(request),
    )


@router.delete(
    "/{product_id}",
    response_model=SuccessResponse[ProductRead],
    response_model_exclude_none=True,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Product not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Product is referenced by a transaction",
        },
        **COMMON_ERROR_RESPONSES,
    },
    summary="Delete a product permanently",
)
async def delete_product(
    request: Request,
    database_path: Annotated[Path, Depends(get_database_path)],
    product_id: Annotated[int, PathParameter(gt=0)],
) -> SuccessResponse[ProductRead]:
    try:
        row = await delete_product_record(product_id, database_path=database_path)
    except sqlite3.IntegrityError as exception:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.PRODUCT_IN_USE,
            message="Product cannot be deleted because it has transaction history",
        ) from exception
    if row is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product not found",
        )

    return SuccessResponse(
        message="Product deleted successfully",
        data=ProductRead(**dict(row)),
        meta=build_response_meta(request),
    )
