from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SERVER_HOST: str
    SERVER_PORT: int
    APP_NAME: str
    
    DB_NAME: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_SECRET: str
    SECRET_KEY: str
    JWT_ALGORITHM: str
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_CLIENT_SECRET: str

    class Config:
        env_file = ".env"
        
        
@lru_cache()
def get_settings():
    return Settings()