from fastapi import FastAPI

from app.auth.routes import user
from app.config.database import engine,Base
from app.config.settings import settings_env

settings= settings_env

Base.metadata.create_all(bind=engine)

def create_application():
    application=FastAPI()
    application.include_router(user.user_router)
    application.include_router(user.guest_router)
    application.include_router(user.oauth_router)
    return application


app = create_application()

@app.get("/")
async def root():
    return {"application":"is running!"}


