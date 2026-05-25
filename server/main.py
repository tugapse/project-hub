from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

from fastapi.staticfiles import StaticFiles

from entities.dto import Project
from middleware import MIMETypeFixerMiddleware
from services.database import ProjectsDatabase
from routers import auth as auth_router


# --- Configuration ---
# Use environment variable or default to a local path


app = FastAPI()

app.include_router(auth_router.router)

app.add_middleware(MIMETypeFixerMiddleware)
# Enable CORS for Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database = ProjectsDatabase()
database.load_from_disk()

@app.get("/projects", response_model=List[Project])
def get_projects():
    return database.get_projects()

@app.post("/projects")
def update_projects(incoming_projects: List[Project]):
    database.save_to_disk(incoming_projects)
    return {"status": "success", "count": len(database.get_projects())}

FRONTEND_BUILD_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_BUILD_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="static_app")

if __name__ == "__main__":
    import uvicorn
    host: str = os.getenv("PROJECT_HUB_HOST", "0.0.0.0")
    port = int(os.getenv("PROJECT_HUB_PORT", 9998))
    uvicorn.run(app, host=host, port=port)