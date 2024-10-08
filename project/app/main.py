from fastapi import FastAPI
import logging

from app.auth.routes import user
from app.core.database import engine, Base
from app.core.config import settings_env

# Initialize logger
logger = logging.getLogger(__name__)

# Load settings
settings = settings_env

# Create database tables if they do not exist
try:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")
except Exception as db_creation_error:
    logger.error(f"Error creating database tables: {str(db_creation_error)}")

# Function to create FastAPI application
def create_application():
    logger.info("Starting FastAPI application...")
    application = FastAPI()

    # Include routers from the user module
    try:
        logger.info("Including user routers...")
        application.include_router(user.user_router)
        application.include_router(user.guest_router)
        application.include_router(user.oauth_router)
        logger.info("User routers included successfully.")
    except Exception as route_inclusion_error:
        logger.error(f"Error including user routers: {str(route_inclusion_error)}")

    return application

# Create the FastAPI app
app = create_application()

# Root endpoint
@app.get("/")
async def root():
    logger.info("Root endpoint accessed.")
    return {"application": "is running!"}
