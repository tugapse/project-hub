export enum ProjectStatus {
  NOT_STARTED = 'not_started',
  ACTIVE = 'active',
  ARCHIVED = 'archived',
}

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
  checklistTitle: string;
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
  status: ProjectStatus;
}

export const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  [ProjectStatus.NOT_STARTED]: 'Not started',
  [ProjectStatus.ACTIVE]: 'Active',
  [ProjectStatus.ARCHIVED]: 'Archived',
};
