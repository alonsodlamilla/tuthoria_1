from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, status
from loguru import logger

from .routes import conversation
from .database import connect_to_database, close_database_connection, Database
from .utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup logging
    setup_logging()
    logger.info("Starting up Chat Service API")

    # Startup
    try:
        await connect_to_database()
        logger.info("Successfully connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

    yield

    # Shutdown
    try:
        await close_database_connection()
        logger.info("Successfully closed database connection")
    except Exception as e:
        logger.error(f"Error closing database connection: {str(e)}")


app = FastAPI(title="Chat Service API", lifespan=lifespan)

app.include_router(conversation.router, tags=["conversations"])


@app.get("/health")
async def health_check():
    try:
        await Database.client.server_info()
        logger.debug("Health check passed")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)},
        )
