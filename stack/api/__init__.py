import os
import uvicorn
from .server import app


def serve():
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
