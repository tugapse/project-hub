import json
import os
from pathlib import Path
from typing import List

from ..entities.dto import Project, ProjectStatus
from .storage import write_json_atomic

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROJECTS_JSON_FILE = os.getenv("PROJECT_HUB_JSON_FILE", str(PROJECT_ROOT / "data" / "projects.json"))
ARCHIVED_PROJECTS_JSON_FILE = f"{PROJECTS_JSON_FILE.rsplit('.', 1)[0]}_archived.json"

DB_FILE = Path(PROJECTS_JSON_FILE)
ARCHIVED_DB_FILE = Path(ARCHIVED_PROJECTS_JSON_FILE)


class DatabaseError(Exception):
    """Raised when the projects cannot be persisted."""


class ProjectsDatabase:

    _projects_storage: List[Project]
    _archived_projects_storage: List[Project]

    def __init__(self):
        self._projects_storage = []
        self._archived_projects_storage = []

    def get_projects(self) -> List[Project]:
        return [p for p in self._projects_storage + self._archived_projects_storage if p is not None]

    def load_from_disk(self):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._archived_projects_storage = self.load_json_file(ARCHIVED_DB_FILE)
        self._projects_storage = self.load_json_file(DB_FILE)

    def save_to_disk(self, incoming_projects: List[Project]):
        """Persists the projects, splitting active and archived into separate files.

        Files are written atomically and the in-memory state only changes
        once both files are safely on disk.
        """
        sanitized = self.sanitize_projects(incoming_projects)
        try:
            self._write_json_atomic(DB_FILE, sanitized["active"])
            self._write_json_atomic(ARCHIVED_DB_FILE, sanitized["archived"])
        except OSError as e:
            raise DatabaseError(f"Failed to save projects: {e}") from e

        self._projects_storage = sanitized["active"]
        self._archived_projects_storage = sanitized["archived"]

    def sanitize_projects(self, projects: List[Project]) -> dict[str, List[Project]]:
        """Splits projects into archived and non-archived (active / not started)."""
        archived = [p for p in projects if p.status == ProjectStatus.ARCHIVED]
        active = [p for p in projects if p.status != ProjectStatus.ARCHIVED]
        return {"active": active, "archived": archived}

    def load_json_file(self, file_path: Path) -> List[Project]:
        """Loads projects from a specified JSON file."""
        if file_path.exists() and file_path.stat().st_size > 0:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [Project(**p) for p in data] if data else []
            except Exception as e:
                print(f"⚠️ Load Error from {file_path}: {e}")
                return []
        return []

    @staticmethod
    def _write_json_atomic(path: Path, projects: List[Project]):
        write_json_atomic(path, [p.model_dump(mode="json") for p in projects])
