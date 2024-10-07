import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()


if __name__ == "__main__":
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = os.getenv("SERVER_PORT", "8000")
    
    uvicorn.run("app.main:app", host=host,port=int(port), reload=False)
