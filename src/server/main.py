import mimetypes
from pathlib import Path
from typing import List

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .entities.dto import Project
from .services.database import DatabaseError, ProjectsDatabase

# Some systems (e.g. Windows registry, minimal containers) map these wrongly,
# which breaks loading the Angular bundle as ES modules.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")

FRONTEND_BUILD_DIR = Path(__file__).resolve().parents[2] / "dist"

app = FastAPI(title="Project Hub")

database = ProjectsDatabase()
database.load_from_disk()

api = APIRouter(prefix="/api")


@api.get("/projects", response_model=List[Project])
def get_projects():
    return database.get_projects()


@api.post("/projects")
def update_projects(incoming_projects: List[Project]):
    try:
        database.save_to_disk(incoming_projects)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"status": "success", "count": len(database.get_projects())}


app.include_router(api)

if FRONTEND_BUILD_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="static_app")
