"""Error handling middleware with standardized error responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import logging

logger = logging.getLogger(__name__)


async def error_handler(request: Request, call_next):
    """Global error handler middleware.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response
    """
    try:
        response = await call_next(request)
        return response
    except RequestValidationError as e:
        logger.error(f"Validation error: {e}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": e.errors(),
            },
        )
    except StarletteHTTPException as e:
        logger.error(f"HTTP error: {e.status_code} - {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.detail if isinstance(e.detail, str) else "HTTP_ERROR",
                "message": str(e.detail),
            },
        )
    except Exception as e:
        logger.error(f"Unhandled error: {e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An internal error occurred",
                "details": str(e) if logger.level == logging.DEBUG else None,
            },
        )

