from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# -------------------
# 1. Handle HTTPException
# -------------------
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "type": "HTTPException"
        }
    )

# -------------------
# 2. Handle Validation Errors
# -------------------
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request data",
            "details": exc.errors(),
            "type": "RequestValidationError"
        }
    )

# -------------------
# 3. Handle ValueError
# -------------------
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error": str(exc),
            "type": "ValueError"
        }
    )

# -------------------
# 4. Handle All Other Exceptions (Global Handler)
# -------------------
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "details": str(exc),
            "type": "GeneralException"
        }
    )
