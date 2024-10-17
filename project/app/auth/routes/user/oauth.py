import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordBearer
from fastapi.responses import RedirectResponse

from app.core import get_db, settings_env
from app.auth.services import get_auth_callback

settings = settings_env


logger = logging.getLogger(__name__)

oauth2_password_scheme = OAuth2PasswordBearer(tokenUrl="login")
google_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token"
)

oauth_router = APIRouter(
    prefix="/oauth",
    tags=["OAuth"]
)

# Google Login
@oauth_router.get('/google-login')
async def google_login():
    logger.debug(f"Initiating Google login redirect to: {settings_env.GOOGLE_REDIRECT_URI}")
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings_env.GOOGLE_CLIENT_ID}&redirect_uri={settings_env.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline")

# Google auth callback
@oauth_router.get("/auth/google")
async def auth_google(code: str, session: AsyncSession = Depends(get_db)):
    logger.debug(f"Received authorization code from Google: {code}")
    auth_response = await get_auth_callback(code, session)
    logger.info("Successfully processed Google authentication callback.")
    return auth_response
