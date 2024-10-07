from sqlalchemy.orm import Session
from fastapi import APIRouter, BackgroundTasks, Depends, status, Header, HTTPException,Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

import requests

from app.config.database import get_db
from app.responses.user import UserResponse, LoginResponse
from app.schemas.user import RegisterUserRequest, VerifyUserRequest, LoginRequest, EmailRequest, ResetRequest
from app.services import user
from app.config.settings import get_settings
from app.config import security


settings = get_settings()


templates = Jinja2Templates(directory="app/templates")


user_router = APIRouter(
   prefix="/users",
   tags=["Users"]
)

guest_router = APIRouter(
   prefix="/auth",
   tags=["Auth"]
)

oauth_router = APIRouter(
   prefix="/users",
   tags=["OAuth"]
)


@oauth_router.route('/google/login')
async def login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI  # This creates the url for our /auth endpoint
    return await oauth.google.authorize_redirect(request, redirect_uri)


@oauth_router.route('/google')
async def auth(request: Request, session: Session = Depends(get_db)):
    oauth_data = {'request': request}  
    return await user.get_oauth_login_token(oauth_data, session)

    
@user_router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
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


