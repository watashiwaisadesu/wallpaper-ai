import uvicorn
from app.config.settings import settings_env
settings = settings_env

if __name__ == "__main__":
    host = settings.SERVER_HOST
    port = settings.SERVER_PORT
    uvicorn.run("app.main:app", host=host,port=int(port), reload=True)
