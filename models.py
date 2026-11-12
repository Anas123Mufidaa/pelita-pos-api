from datetime import datetime
from enum import Enum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sku: str = Field(min_length=1, max_length=50)
    nama: str = Field(min_length=1, max_length=100)
    kategori: str = Field(min_length=1, max_length=100)
    harga: int = Field(ge=0)
    stok: int = Field(ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int = Field(gt=0)


class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    cashier_name: str = Field(min_length=1, max_length=100)


class TransactionRead(BaseModel):
    id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)
    total_price: int = Field(ge=0)
    cashier_name: str
    status: TransactionStatus
    created_at: str


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    PRODUCT_IN_USE = "PRODUCT_IN_USE"
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
