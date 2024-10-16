from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import MetaData


from app.core import settings_env

settings = settings_env


engine = create_async_engine(settings.DB_URL_ASYNC, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


Base = declarative_base()
# meta = MetaData(bind=engine)
# meta.reflect()
# meta.drop_all()
# print("All tables dropped!")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
