import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
class Settings(BaseSettings):
    SERVER_HOST: str = os.getenv("SERVER_HOST")
    SERVER_PORT: str = os.getenv("SERVER_PORT")
    APP_NAME: str = os.getenv("APP_NAME")

    DB_NAME: str = os.getenv("DB_NAME")
    DB_USERNAME: str = os.getenv("DB_USERNAME")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")

    MAIL: str = os.getenv("MAIL")
    MAIL_SERVER: str = os.getenv("MAIL_SERVER")
    MAIL_APP_PASSWORD: str = os.getenv("MAIL_APP_PASSWORD")

    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 30))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")

    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")

    EXTERNAL_LIBRARY_LEVEL_LOG: str = os.getenv("EXTERNAL_LIBRARY_LEVEL_LOG")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL")

    @property
    def DB_URL_SYNC(self):
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DB_URL_ASYNC(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings_env = Settings()
