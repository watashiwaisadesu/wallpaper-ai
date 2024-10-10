from fastapi import FastAPI

from app.auth.routes import auth_router
from app.rooms.routes import room_router
from app.core import engine, Base, settings_env


settings = settings_env
Base.metadata.create_all(bind=engine)


def create_application():
    application = FastAPI()
    application.include_router(auth_router)
    application.include_router(room_router)
    return application


app = create_application()


@app.get("/")
async def root():
    return {"application": "is running!"}
