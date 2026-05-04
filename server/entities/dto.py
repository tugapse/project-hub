# --- Data Models ---
from typing import List, Optional

from pydantic import BaseModel


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
    archived: bool = False
