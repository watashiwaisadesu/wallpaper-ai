from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVER_HOST: str
    APP_NAME: str
    
    DB_NAME: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    # DB_URL :  str = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_SECRET: str
    SECRET_KEY: str
    JWT_ALGORITHM: str
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_CLIENT_SECRET: str
    
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str

    class Config:
        env_file = "..env"
        

settings_env = Settings()

