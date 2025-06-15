import logging
import traceback
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors during request processing"""
        try:
            # Skip error handling for excluded paths
            if any(request.url.path.startswith(path) for path in self.exclude_paths):
                return await call_next(request)
            
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            logger.warning(f"HTTP Exception: {e.status_code} - {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail, "type": "http_exception"}
            )
            
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "type": "internal_error",
                    "message": "An unexpected error occurred. Please try again later."
                }
            )

def create_error_handler_middleware(app, exclude_paths: list = None):
    """Factory function to create error handler middleware"""
    return ErrorHandlerMiddleware(app, exclude_paths) 