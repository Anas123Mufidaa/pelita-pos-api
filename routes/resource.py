import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path as PathParameter,
    Query,
    Request,
    Response,
    status,
)

from database import fetch_product, fetch_products, get_database_path, insert_product
from exceptions import AppException
from models import (
    ErrorCode,
    ErrorResponse,
    PaginationMeta,
    ProductCreate,
    ProductRead,
    SuccessResponse,
)
from responses import build_response_meta


router = APIRouter(prefix="/resource", tags=["Dashboard"])

COMMON_ERROR_RESPONSES = {
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
}


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
        if "products.sku" in str(exception):
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code=ErrorCode.DUPLICATE_RESOURCE,
                message="Product SKU already exists",
            ) from exception
        raise

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
