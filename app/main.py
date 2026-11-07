from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from app.helpers.config import (
    API_VERSION,
    API_BASE_NAME
)
from app.helpers.exception import (
    http_exception_handler,
    validation_exception_handler,
    value_error_handler,
    global_exception_handler
)
from app.helpers.databaseConnection import engine, Base
from app.routers import (chatRouter)

app  = FastAPI()

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

@app.post(f"/{API_BASE_NAME}/{API_VERSION}/database/create-tables", tags=["database"])
async def create_database_tables():
    """Create missing application tables without modifying existing tables."""
    expected_tables = set(Base.metadata.tables)

    try:
        async with engine.begin() as conn:
            existing_tables = await conn.run_sync(
                lambda sync_conn: set(inspect(sync_conn).get_table_names())
            )
            missing_tables = expected_tables - existing_tables

            if not missing_tables:
                return {
                    "status": "success",
                    "message": "All database tables already exist; no changes were made.",
                    "created_tables": [],
                    "already_existing_tables": sorted(expected_tables),
                }

            # The document models use pgvector's vector column type.
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

        return {
            "status": "success",
            "message": "Missing database tables were created.",
            "created_tables": sorted(missing_tables),
            "already_existing_tables": sorted(existing_tables),
        }
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to create database tables. Check the database connection and permissions.",
        ) from exc


app.include_router(chatRouter.router, prefix=f"/{API_BASE_NAME}/{API_VERSION}")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    for path_item in openapi_schema["paths"].values():
        operation = path_item.get("post", {})
        if not operation.get("operationId", "").startswith("file_upload_"):
            continue

        request_schema = operation["requestBody"]["content"]["multipart/form-data"]["schema"]
        schema_name = request_schema["$ref"].rsplit("/", 1)[-1]
        file_item_schema = openapi_schema["components"]["schemas"][schema_name]["properties"]["files"]["items"]
        file_item_schema["format"] = "binary"
        file_item_schema.pop("contentMediaType", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

@app.get("/")
def read_root():
    return {"Hello": "World"}