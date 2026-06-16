import { ProjectStatus } from "./enums";

export interface ChecklistItem {
  text: string;
  completed: boolean;
}

export interface Task {
  notes: any;
  id: number;
  content: string;
  description: string;
  color: string;
  icon: string;
  checklistTitle:string;
  checklist: ChecklistItem[];
}
export interface Column { id: string; title: string; tasks: Task[]; }
export interface Project { id: string; name: string; columns: Column[]; status:ProjectStatus; archived: boolean; }

