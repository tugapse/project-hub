from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import json
import os

# --- Configuration ---
# Use environment variable or default to a local path
PROJECTS_JSON_FILE = os.getenv("PROJECT_HUB_JSON_FILE", "./data/projects.json")
DB_FILE = Path(PROJECTS_JSON_FILE)

app = FastAPI()

# Enable CORS for Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
class ChecklistItem(BaseModel):
    text: str
    completed: bool

class Task(BaseModel):
    id: int
    content: str
    description: Optional[str] = ""
    color: Optional[str] = "#ccc"
    icon: Optional[str] = "📄"
    isEditing: Optional[bool] = False
    checklist: Optional[List[ChecklistItem]] = []
    notes: Optional[str] = ""

class Column(BaseModel):
    id: str
    title: str
    tasks: List[Task]

class Project(BaseModel):
    id: str
    name: str
    columns: List[Column]

# --- Global Storage ---
PROJECTS_STORAGE: List[Project] = []

def load_from_disk():
    global PROJECTS_STORAGE
    
    # 1. Create the folder if it doesn't exist
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 2. Check if file exists and is not empty
    if DB_FILE.exists() and DB_FILE.stat().st_size > 0:
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                PROJECTS_STORAGE = [Project(**p) for p in data] if data else []
            print(f"✅ Loaded {len(PROJECTS_STORAGE)} projects from {DB_FILE}")
        except Exception as e:
            print(f"⚠️ Load Error: {e}")
            PROJECTS_STORAGE = []
    else:
        # 3. Initialize file if missing or empty
        save_to_disk() 
        print(f"📁 Initialized new DB at {DB_FILE}")

def save_to_disk():
    """Dumps the current in-memory state to the JSON file."""
    try:
        # Ensure directory exists before saving
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(DB_FILE, "w", encoding="utf-8") as f:
            data = [p.model_dump() for p in PROJECTS_STORAGE]
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ Failed to save to disk: {e}")

# Initial Load
load_from_disk()

# --- API Routes ---

@app.get("/projects", response_model=List[Project])
def get_projects():
    return PROJECTS_STORAGE

@app.post("/projects")
def update_projects(incoming_projects: List[Project]):
    global PROJECTS_STORAGE
    PROJECTS_STORAGE = incoming_projects
    save_to_disk()
    return {"status": "success", "count": len(PROJECTS_STORAGE)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)