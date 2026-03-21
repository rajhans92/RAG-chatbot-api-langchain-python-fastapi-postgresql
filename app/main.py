from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
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

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(chatRouter.router, prefix='/{API_BASE_NAME}/{API_VERSION}')

@app.get("/")
def read_root():
    return {"Hello": "World"}