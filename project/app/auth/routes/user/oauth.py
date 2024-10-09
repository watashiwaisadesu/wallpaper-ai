import logging
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Header, Request, Security
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.responses import RedirectResponse


from app.core import get_db, settings_env
from app.auth.services import get_auth_callback

settings = settings_env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

google_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token"
)

github_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://github.com/login/oauth/authorize",
    tokenUrl="https://github.com/login/oauth/access_token"
)

oauth_router = APIRouter(
    prefix="/oauth",
    tags=["OAuth"]
)

# Google Login
@oauth_router.get('/google-login')
async def login(request: Request):
    logger.info("Starting Google login process")
    logger.debug(f"GOOGLE_CLIENT_ID: {settings.GOOGLE_CLIENT_ID}")
    logger.debug(f"GOOGLE_REDIRECT_URI: {settings.GOOGLE_REDIRECT_URI}")
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline")


# Google auth callback
@oauth_router.get('/auth/google')
async def auth_google(code: str, session: Session = Depends(get_db)):
    logger.info("Received Google auth callback")
    provider = "google"
    return await get_auth_callback(code, provider, session)
