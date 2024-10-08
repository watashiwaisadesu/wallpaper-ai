from sqlalchemy.orm import Session
from fastapi import APIRouter, BackgroundTasks, Depends, status, Header, HTTPException,Request, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer,OAuth2AuthorizationCodeBearer,SecurityScopes
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.database import get_db
from app.responses.user import UserResponse, LoginResponse
from app.auth.schemas.user import RegisterUserRequest, VerifyUserRequest, LoginRequest, EmailRequest, ResetRequest
from app.auth.services import user
from app.core.config import settings_env
from app.core import security

settings = settings_env
templates = Jinja2Templates(directory="app/templates")

# oauth2 Schema
google_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token"
)


github_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://github.com/login/oauth/authorize",
    tokenUrl="https://github.com/login/oauth/access_token"
)


user_router = APIRouter(
   prefix="/users",
   tags=["Users"]
)


guest_router = APIRouter(
   prefix="/auth",
   tags=["Auth"]
)


oauth_router = APIRouter(
    prefix="/oauth",
    tags=["OAuth"]
)

# GitHub Login
# @oauth_router.get('/github-login')
# async def github_login():
#     return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}", status_code=302)

# github calback function
# @oauth_router.get("/auth/callback")
# async def auth_callback(code: str, session: Session = Depends(get_db)):
#     provider = "github"
#     return await user.get_auth_callback(code, provider, session)
        
@oauth_router.get('/google-login')
async def login(request: Request):
    print(settings.GOOGLE_CLIENT_ID)
    print(settings.GOOGLE_REDIRECT_URI)
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline")


@oauth_router.get('/auth/google')
async def auth_google(code: str, session: Session = Depends(get_db)):
    provider = "google"
    return await user.get_auth_callback(code, provider, session)

    
@user_router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user_account(data: RegisterUserRequest,backgroundTasks: BackgroundTasks, session: Session = Depends(get_db)): 
    return await user.create_user_account(data,backgroundTasks,session)

@user_router.get('/verify')
async def verify_user_account_get(request: Request, token: str, email: str, backgroundTasks: BackgroundTasks, session: Session = Depends(get_db)):
    data = VerifyUserRequest(token=token, email=email)
    
    activation_successful = await verify_user_account(data,backgroundTasks,session)
    
    if activation_successful:
        return templates.TemplateResponse("account_activated.html", {"request": request})
    else:
        raise HTTPException(status_code=400, detail="Activation failed.")

@user_router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_user_account(data: VerifyUserRequest,backgroundTasks: BackgroundTasks,  session: Session = Depends(get_db)):
    return await user.activate_user_account(data,backgroundTasks,session)

@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def fetch_user(user = Depends(security.get_current_user)):
    return user

@guest_router.post("/login", status_code=200, response_model=LoginResponse)
async def user_login(data: LoginRequest,session: Session = Depends(get_db)):
    return await user.get_login_token(data, session)


@guest_router.post("/refresh", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def refresh_token(refresh_token = Header(), session: Session = Depends(get_db)):
    return await user.get_refresh_token(refresh_token, session)


@guest_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: EmailRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_db)):
    await user.email_forgot_password_link(data, background_tasks, session)
    return {"message": "A email with password reset link has been sent to you."}


@guest_router.put("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetRequest, session: Session = Depends(get_db)):
    await user.reset_user_password(data, session)
    return {"message": "Your password has been updated."}






