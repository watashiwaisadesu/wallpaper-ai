from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVER_HOST: str
    SERVER_PORT: str
    APP_NAME: str
    
    DB_NAME: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str

    MAIL: str
    MAIL_SERVER: str
    MAIL_APP_PASSWORD: str
    
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_SECRET: str
    SECRET_KEY: str
    JWT_ALGORITHM: str
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_CLIENT_SECRET: str

    EXTERNAL_LIBRARY_LEVEL_LOG: str
    LOG_LEVEL: str
    class Config:
        env_file = ".env"

    @property
    def DB_URL_SYNC(self):
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DB_URL_ASYNC(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings_env = Settings()

