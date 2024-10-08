from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
import logging

from app.core.config import settings_env

# Initialize logger
logger = logging.getLogger(__name__)

settings = settings_env

DB_URL = f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
logger.info(f"Connecting to database at: {DB_URL}")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    session = SessionLocal()
    logger.info("Database session created")
    try:
        yield session
    finally:
        session.close()
        logger.info("Database session closed")
