import pytest
import asyncio
from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient

# Load test environment variables
os.environ["ENVIRONMENT"] = "test"
load_dotenv(".env.test")

# Import app after environment is set
from main import app
from database import get_database, Database

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_app():
    """Create a test client instance."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(autouse=True)
async def clean_db():
    """Clean the database before and after each test."""
    # Get test database
    db = await get_database()
    
    # Clean up before test
    await db.conversations.delete_many({})
    await db.user_states.delete_many({})
    
    yield
    
    # Clean up after test
    await db.conversations.delete_many({})
    await db.user_states.delete_many({}) 