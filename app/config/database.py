from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine

from .settings import get_settings

settings=get_settings()

DB_URL = f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine= create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False,autoflush=False)
Base = declarative_base()

def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

