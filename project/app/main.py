from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import logging

from app.auth.routes import auth_router
from app.rooms.routes import room_router
from app.core import settings_env
from app.db.logging import setup_logging
from app.products.routes import product_router


settings = settings_env
logger = logging.getLogger(__name__)

origins = [
    "https://ai-wallpapers-kz.netlify.app",
    "https://wallpaper-ai-3m94.onrender.com",
    "https://redirect-frontend.netlify.app"
]
def create_application() -> FastAPI:
    application = FastAPI()

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Set-Cookie",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Origin",
            "X-Requested-With",
            "X-CSRF-Token"
        ],
    )
    application.include_router(auth_router)
    application.include_router(room_router)
    application.include_router(product_router)
    return application

app = create_application()

@app.on_event("startup")
async def startup_event():
    setup_logging()

@app.get("/")
async def root():
    logger.debug("Redirecting to FRONTEND..")
    return RedirectResponse(url=f"{settings.SERVER_HOST}/")




