from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
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

@app.get("/")
def read_root():
    return {"Hello": "World"}