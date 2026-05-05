export interface ChecklistItem {
  text: string;
  completed: boolean;
}

export interface Task {
  id: number;
  content: string;
  description: string;
  color: string;
  icon: string;
  checklist: ChecklistItem[];
  notes: string;
}

export interface Column {
  id: string;
  title: string;
  tasks: Task[];
}

export interface Project {
  id: string;
  name: string;
  columns: Column[];
}