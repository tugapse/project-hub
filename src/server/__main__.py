import os

import uvicorn

from .main import app

if __name__ == "__main__":
    host = os.getenv("PROJECT_HUB_HOST", "0.0.0.0")
    port = int(os.getenv("PROJECT_HUB_PORT", 9998))
    uvicorn.run(app, host=host, port=port)
