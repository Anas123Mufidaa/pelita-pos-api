from datetime import datetime
from enum import Enum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    TRANSACTION_CONFLICT = "TRANSACTION_CONFLICT"
    TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
    INVALID_TRANSACTION_STATE = "INVALID_TRANSACTION_STATE"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    details: list[ErrorDetail] | None = None


class PaginationMeta(BaseModel):
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    total: int = Field(ge=0)
    has_next: bool


class ResponseMeta(BaseModel):
    request_id: str
    timestamp: datetime
    pagination: PaginationMeta | None = None


DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    success: Literal[True] = True
    message: str
    data: DataT
    meta: ResponseMeta


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorBody
    meta: ResponseMeta
