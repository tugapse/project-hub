interface ChecklistItem {
  text: string;
  completed: boolean;
}

interface Task {
  notes: any;
  id: number;
  content: string;
  description: string;
  color: string;
  icon: string;
  checklist: ChecklistItem[];
}
interface Column { id: string; title: string; tasks: Task[]; }
interface Project { id: string; name: string; columns: Column[]; }
