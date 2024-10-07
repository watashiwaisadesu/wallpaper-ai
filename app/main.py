from fastapi import FastAPI,APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware
import requests
from jose import jwt

from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from app.routes import user
from app.config.database import engine,Base
from app.config.settings import get_settings

settings= get_settings()

Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_application():
    application=FastAPI()
    application.include_router(user.user_router)
    application.include_router(user.guest_router)
    application.include_router(user.oauth_router)
    return application



config_data = {'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': settings.GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

app = create_application()
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

@app.get("/")
async def root():
    return {"application":"is running!"}


