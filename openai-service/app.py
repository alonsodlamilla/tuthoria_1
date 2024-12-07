from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from shared.templates.prompts import TEMPLATES
from services.db_client import DBClient
from config.settings import get_settings, Settings

app = FastAPI()
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
db_client = DBClient()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

# Add your routes here
