from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os

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

# --- In-Memory Storage ---
# --- GLOBAL STORAGE ---
DB_FILE = "projects.json"
PROJECTS_STORAGE: List[Project] = []

def load_from_disk():
    global PROJECTS_STORAGE
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                # Ensure we handle empty files safely
                if not data:
                    PROJECTS_STORAGE = []
                else:
                    PROJECTS_STORAGE = [Project(**p) for p in data]
            print(f"✅ Loaded {len(PROJECTS_STORAGE)} projects into RAM.")
        except Exception as e:
            print(f"⚠️ Load Error: {e}")
            PROJECTS_STORAGE = []
    else:
        # Create empty file if it doesn't exist to prevent read errors
        with open(DB_FILE, "w") as f:
            json.dump([], f)
        PROJECTS_STORAGE = []

# CRITICAL: Run this BEFORE the FastAPI app starts
load_from_disk()

def save_to_disk():
    """Dumps the current in-memory state to the JSON file."""
    try:
        with open(DB_FILE, "w") as f:
            # Convert models to dictionaries for JSON serialization
            data = [p.model_dump() for p in PROJECTS_STORAGE]
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ Failed to save to disk: {e}")

# Trigger initial load
load_from_disk()

# --- API Routes ---

@app.get("/projects", response_model=List[Project])
def get_projects():
    """Returns the current state from memory."""
    return PROJECTS_STORAGE

@app.post("/projects")
def update_projects(incoming_projects: List[Project]):
    """Updates memory and triggers a background disk save."""
    global PROJECTS_STORAGE
    PROJECTS_STORAGE = incoming_projects
    save_to_disk()
    return {"status": "success", "count": len(PROJECTS_STORAGE)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)