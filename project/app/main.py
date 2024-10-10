from fastapi import FastAPI

from app.auth.routes import auth_router
from app.core import engine, Base, settings_env

# Load settings
settings = settings_env

Base.metadata.create_all(bind=engine)

# Function to create FastAPI application
def create_application():
    application = FastAPI()
    application.include_router(auth_router)
    return application

# Create the FastAPI app
app = create_application()

# Root endpoint
@app.get("/")
async def root():
    return {"application": "is running!"}
