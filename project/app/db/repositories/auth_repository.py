from datetime import datetime
from sqlalchemy.orm import joinedload

from app.db.models import  UserToken

def get_user_token_by_keys(refresh_key, access_key, user_id, session):
    return session.query(UserToken).options(joinedload(UserToken.user)).filter(
        UserToken.refresh_key == refresh_key,
        UserToken.access_key == access_key,
        UserToken.owner_id == user_id,
        UserToken.expires_at > datetime.utcnow()
    ).first()