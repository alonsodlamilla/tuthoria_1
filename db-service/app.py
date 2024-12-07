import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from logging_config import setup_logging
from database import connect_to_database, close_database_connection
from routes import health, conversation

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DB Service")
    await connect_to_database()
    yield
    await close_database_connection()
    logger.info("Shutting down DB Service")

app = FastAPI(
    title="DB Service",
    description="Database service for TuthorIA",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(conversation.router, prefix="/api/v1", tags=["conversations"]) 