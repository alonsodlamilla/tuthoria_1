from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Dict
from database import get_database

router = APIRouter()


@router.get(
    "/health",
    response_model=Dict[str, str],
    summary="Health Check",
    description="Check the health status of the DB service and MongoDB connection",
)
async def health_check():
    try:
        # Test MongoDB connection
        db = await get_database()
        await db.command("ping")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "database": "connected",
                "service": "running",
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "service": "running",
                "error": str(e),
            },
        )
