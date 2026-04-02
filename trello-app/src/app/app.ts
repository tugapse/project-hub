import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import {
  CdkDragDrop,
  DragDropModule,
  moveItemInArray,
  transferArrayItem
} from '@angular/cdk/drag-drop';

// --- Model Interfaces ---
interface ChecklistItem {
  text: string;
  completed: boolean;
}

interface Task {
  id: number;
  content: string;
  description: string;
  color: string;
  icon: string;
  checklist: ChecklistItem[];
  notes: string;
  isEditing?: boolean;
}

interface Column {
  id: string;
  title: string;
  tasks: Task[];
}

interface Project {
  id: string;
  name: string;
  columns: Column[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, DragDropModule, HttpClientModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class AppComponent implements OnInit {
  private http = inject(HttpClient);
  private readonly API_URL = 'http://localhost:8000/projects';

  projects: Project[] = [];
  currentProject: Project | null = null;
  isSyncing = false;
  isDarkMode = true;
  editingProjectId: string | null = null;
  editingTask: Task | null = null;
  originalTask: Task | null = null;
  showPopup = false;

  colors = ['#61bd4f', '#f2d600', '#ff9f1a', '#eb5a46', '#c377e0', '#0079bf'];
  icons = ['📝', '🚀', '🧪', '🐞', '✅', '🔥', '⚙️', '💬'];

  ngOnInit() {
    const savedTheme = localStorage.getItem('preferred-theme') || 'dark';
    this.isDarkMode = savedTheme === 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    this.fetchData();
  }

  fetchData() {
    this.http.get<Project[]>(this.API_URL).subscribe({
      next: (data) => {
        this.projects = data.map(project => ({
          ...project,
          columns: project.columns.map(column => ({
            ...column, // Ensure checklist is initialized if not present in fetched data
            tasks: column.tasks.map(task => ({ ...task, checklist: task.checklist || [], notes: task.notes || '' }))
          }))
        }));
        const lastId = localStorage.getItem('last-project-id');
        this.currentProject = this.projects.find(p => p.id === lastId) || this.projects[0] || null;
      },
      error: (err) => console.error('Connection failed.', err)
    });
  }

  save() {
    this.isSyncing = true;
    this.http.post(this.API_URL, this.projects).subscribe({
      next: () => {
        this.isSyncing = false;
        if (this.currentProject) localStorage.setItem('last-project-id', this.currentProject.id);
      },
      error: () => this.isSyncing = false
    });
  }

  // --- Project Methods ---
  startEditingProject(p: Project) {
    this.editingProjectId = p.id;
    setTimeout(() => {
      const el = document.querySelector('.proj-edit-input') as HTMLInputElement;
      el?.focus();
    }, 50);
  }

  stopEditingProject() {
    this.editingProjectId = null;
    this.save();
  }

  addProject(name: string) {
    if (!name.trim()) return;
    const newP: Project = {
      id: Date.now().toString(),
      name,
      columns: [
        { id: 'todo', title: 'To Do', tasks: [] },
        { id: 'doing', title: 'Doing', tasks: [] },
        { id: 'done', title: 'Done', tasks: [] }
      ]
    };
    this.projects.push(newP);
    this.selectProject(newP);
  }

  selectProject(p: Project) {
    this.currentProject = p;
    this.save();
  }

  deleteProject(p: Project, e: MouseEvent) {
    e.stopPropagation();
    if (confirm(`Delete project "${p.name}"?`)) {
      this.projects = this.projects.filter(proj => proj.id !== p.id);
      this.currentProject = this.projects[0] || null;
      this.save();
    }
  }

  getProjectProgress(project: Project) {
    const todo = project.columns.find(c => c.id === 'todo')?.tasks.length || 0;
    const doing = project.columns.find(c => c.id === 'doing')?.tasks.length || 0;
    const done = project.columns.find(c => c.id === 'done')?.tasks.length || 0;
    const total = todo + doing + done;

    if (total === 0) {
      return { todo: 0, doing: 0, done: 0 };
    }

    return {
      todo: (todo / total) * 100,
      doing: (doing / total) * 100,
      done: (done / total) * 100,
    };
  }

  openTaskPopup(task: Task) {
    this.originalTask = task; // Keep a reference to the original task
    this.editingTask = { ...task }; // Edit a copy
    this.showPopup = true;
  }

  closeTaskPopup() {
    if (this.editingTask) { // originalTask is not strictly needed here if we're just saving the editingTask
      // Find and update the original task
      const project = this.projects.find(p => p.columns.some(c => c.tasks.some(t => t.id === this.editingTask!.id)));
      if (project && this.originalTask) { // Only update if originalTask exists (meaning it was an existing task)
        const column = project.columns.find(c => c.tasks.some(t => t.id === this.originalTask!.id));
        if (column) {
          const taskIndex = column.tasks.findIndex(t => t.id === this.originalTask!.id);
          if (taskIndex !== -1) {
            column.tasks[taskIndex] = this.editingTask;
          }
        }
      }
      // If it was a new task being edited, it would have been added to the column already.
      // The save() call below handles persisting the current state.
      // If the editingTask was a new task, it would have been added to the column already
      // and this logic ensures its properties are up-to-date before saving.
    }
    this.editingTask = null;
    this.originalTask = null;
    this.showPopup = false;
    this.save();
  }

  cancelEditingTask() {
    this.editingTask = null;
    this.originalTask = null;
    this.showPopup = false;
  }

  // --- Task Methods ---
  addTask(column: Column, content: string) {
    if (!content.trim()) return;
    column.tasks.push({ // Initialize checklist for new tasks
      id: Date.now(), content, description: '', color: '#475569', icon: '📄', checklist: [], notes: ''
    });
    this.save();
  }

  updateTask(key: 'color' | 'icon', value: string) {
    if (!this.editingTask) return;
    if (key === 'color') this.editingTask.color = value;
    if (key === 'icon') this.editingTask.icon = value;
    this.saveTask(); // Save changes immediately
  }

  deleteTask(col: Column, task: Task) {
    if (confirm('Eliminar esta tarefa?')) {
      col.tasks = col.tasks.filter(t => t.id !== task.id);
      this.save();
    }
  }

  clearBoard() {
    if (this.currentProject && confirm('Limpar todas as tarefas deste projeto?')) {
      this.currentProject.columns.forEach(c => c.tasks = []);
      this.save();
    }
  }

  // --- Misc ---
  toggleTheme() {
    this.isDarkMode = !this.isDarkMode;
    const theme = this.isDarkMode ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('preferred-theme', theme);
  }

  drop(event: CdkDragDrop<Task[]>) {
    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    } else {
      transferArrayItem(event.previousContainer.data, event.container.data, event.previousIndex, event.currentIndex);
    }
    this.save();
  }

  // --- Checklist Methods ---
  addChecklistItem(text: string) {
    if (text && this.editingTask) {
      if (!this.editingTask.checklist) {
        this.editingTask.checklist = [];
      }
      this.editingTask.checklist.push({ text, completed: false });
      this.saveTask();
    }
  }

  deleteChecklistItem(index: number) {
    if (this.editingTask && this.editingTask.checklist) {
      this.editingTask.checklist.splice(index, 1);
      this.saveTask();
    }
  }

  getChecklistProgress(task: Task): { completed: number, percentage: number } {
    if (!task.checklist || task.checklist.length === 0) {
      return { completed: 0, percentage: 0 };
    }
    const completed = task.checklist.filter(item => item.completed).length;
    const percentage = (completed / task.checklist.length) * 100;
    return { completed, percentage };
  }

  // This is for auto-saving on blur, etc.
  saveTask() {
    this._updateTaskInProjects();
    this.save();
  }

  private _updateTaskInProjects() {
    if (!this.editingTask || !this.originalTask) return;

    for (const project of this.projects) {
      for (const column of project.columns) {
        const taskIndex = column.tasks.findIndex(t => t.id === this.originalTask!.id);
        if (taskIndex !== -1) {
          Object.assign(column.tasks[taskIndex], this.editingTask);
          return; // Exit after finding and updating
        }
      }
    }
  }
}
