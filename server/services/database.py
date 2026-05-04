
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
    
    def __init__(self):
        self._projects_storage = []
    
    def get_projects(self):
        return self._projects_storage
        
    def load_from_disk(self):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 2. Check if file exists and is not empty
        if DB_FILE.exists() and DB_FILE.stat().st_size > 0:
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._projects_storage = [Project(**p) for p in data] if data else []
                print(f"✅ Loaded {len(self._projects_storage)} projects from {DB_FILE}")
            except Exception as e:
                print(f"⚠️ Load Error: {e}")
                self._projects_storage = []
        else:
            # 3. Initialize file if missing or empty
            self.save_to_disk(self._projects_storage) 
            print(f"📁 Initialized new DB at {DB_FILE}")

    def save_to_disk(self, incomming_projects:list[Project]):
        """Dumps the current in-memory state to the JSON file."""
        try:
            # Ensure directory exists before saving
            DB_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._projects_storage = incomming_projects
            with open(DB_FILE, "w", encoding="utf-8") as f:
                data = [p.model_dump() for p in incomming_projects]
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"❌ Failed to save to disk: {e}")
