from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core import settings_env

settings = settings_env

engine = create_async_engine(settings.DB_URL_ASYNC, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

print(settings.DB_URL_ASYNC)

Base = declarative_base()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

