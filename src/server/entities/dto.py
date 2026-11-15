# --- Data Models ---
from typing import List, Optional
from pydantic import BaseModel, Field
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


# --- Auth ---

class LoginRequest(BaseModel):
    username: str
    password: str

class MeResponse(BaseModel):
    username: str
    token_kind: str

class DeviceCodeRequest(BaseModel):
    client_name: str = Field(default="API client", min_length=1, max_length=100)

class DeviceCodeResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int

class DeviceTokenRequest(BaseModel):
    device_code: str

class DeviceTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class DeviceInfoResponse(BaseModel):
    user_code: str
    client_name: str
    expires_in: int

class DeviceApproveRequest(BaseModel):
    user_code: str
    approve: bool
