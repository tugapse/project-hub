# --- Data Models ---
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class ProjectStatus(Enum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    ARCHIVED = "archived"

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
    checklistTitle:Optional[str] = "" 
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
    status:ProjectStatus = ProjectStatus.ACTIVE
