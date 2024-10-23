from fastapi import APIRouter
from app.auth.routes.user import user_router
from app.auth.routes.guest import guest_router
from app.auth.routes.oauth import oauth_router


auth_router = APIRouter()

auth_router.include_router(user_router)
auth_router.include_router(guest_router)
auth_router.include_router(oauth_router)
