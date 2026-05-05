
import json
import os
from pathlib import Path
from typing import List
from entities.dto import Project

PROJECTS_JSON_FILE = os.getenv("PROJECT_HUB_JSON_FILE", "./data/projects.json")
ARCHIVED_PROJECTS_JSON_FILE = f"{PROJECTS_JSON_FILE.rsplit('.', 1)[0]}_archived.json"

DB_FILE = Path(PROJECTS_JSON_FILE)
ARCHIVED_DB_FILE = Path(ARCHIVED_PROJECTS_JSON_FILE)

class ProjectsDatabase:
    
    _projects_storage: List[Project]
    _archived_projects_storage: List[Project]
    
    def __init__(self):
        self._projects_storage = []
        self._archived_projects_storage = []
    
    def get_projects(self):
        return [project for project in self._projects_storage + self._archived_projects_storage if project is not None]
        
    def load_from_disk(self):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)

        self._archived_projects_storage = self.load_json_file(ARCHIVED_DB_FILE)
        self._projects_storage = self.load_json_file(DB_FILE)
        


    def save_to_disk(self, incomming_projects:list[Project]):
        """Dumps the current in-memory state to the JSON file."""
        try:
            # Ensure directory exists before saving
            DB_FILE.parent.mkdir(parents=True, exist_ok=True)
            ARCHIVED_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            sanitized_projects = self.sanitize_projects(incomming_projects)
            self._projects_storage = sanitized_projects["active"]
            self._archived_projects_storage = sanitized_projects["archived"]

            with open(DB_FILE, "w", encoding="utf-8") as f:
                data = [p.model_dump() for p in self._projects_storage]
                json.dump(data, f, indent=4)
            with open(ARCHIVED_DB_FILE, "w", encoding="utf-8") as f:
                data = [p.model_dump() for p in self._archived_projects_storage]
                json.dump(data, f, indent=4)
      
        except Exception as e:
            print(f"❌ Failed to save to disk: {e}")
    
    def sanitize_projects(self, projects: List[Project]) -> dict[str, List[Project]]:
        """Removes any projects that are archived."""
        active_projects = [p for p in projects if not p.archived]
        archived_projects = [p for p in projects if p.archived]    
        return { "active": active_projects, "archived": archived_projects } 
    
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
    
