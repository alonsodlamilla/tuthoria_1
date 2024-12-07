from fastapi import FastAPI
from loguru import logger
from contextlib import asynccontextmanager

from database import connect_to_database, close_database_connection
from routes import conversation

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DB Service")
    await connect_to_database()
    yield
    await close_database_connection()
    logger.info("Shutting down DB Service")

app = FastAPI(
    title="DB Service",
    description="Database service for chat application",
    lifespan=lifespan
)

app.include_router(conversation.router, prefix="/api/v1", tags=["conversations"])
