from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request, Response

from models import PaginationMeta, ResponseMeta


def build_response_meta(
    request: Request,
    pagination: PaginationMeta | None = None,
) -> ResponseMeta:
    request_id = getattr(request.state, "request_id", None) or f"req_{uuid4().hex}"
    return ResponseMeta(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc),
        pagination=pagination,
    )


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = f"req_{uuid4().hex}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
