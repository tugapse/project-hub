import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TaskModalComponent } from "../components/modal/modal";
import { Column, Project, Task } from '../entities/interfaces';
import { ApiService } from '../services/api.service';
import { MainViewComponent } from './main-view/main-view.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { ProjectStatus } from '../entities/enums';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule, TaskModalComponent, SidebarComponent, MainViewComponent],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class AppComponent implements OnInit {
  private apiService = inject(ApiService);

  projects: Project[] = [];
  currentProject: Project | null = null;
  isSyncing = false;
  isDarkMode = true;
  isSidebarCollapsed = false;

  // Modal State
  editingTask: Task | null = null;
  showPopup = false;

  ngOnInit() {
    const savedTheme = localStorage.getItem('preferred-theme') || 'light';
    this.isDarkMode = savedTheme === 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    this.fetchData();
  }

  fetchData() {
    this.apiService.fetchData().subscribe(projects => {
      this.projects = projects;
      const lastProjectId = localStorage.getItem('last-project-id');
      if (lastProjectId) {
        this.currentProject = this.projects.find(p => p.id === lastProjectId) || this.projects[0] || null;
      } else {
        this.currentProject = this.projects[0] || null;
      }
    });
  }

  save() {
    this.isSyncing = true;
    this.apiService.save(this.projects).subscribe({
      next: () => {
        this.isSyncing = false;
        if (this.currentProject) {
          localStorage.setItem('last-project-id', this.currentProject.id);
        }
      },
      error: () => this.isSyncing = false
    });
  }

  // --- Project Event Handlers ---
  handleProjectAdded(name: string) {
    if (!name.trim()) return;
    const newP: Project = {
      id: Date.now().toString(),
      name,
      columns: [
        { id: 'todo', title: 'To Do', tasks: [] },
        { id: 'doing', title: 'Doing', tasks: [] },
        { id: 'done', title: 'Done', tasks: [] }
      ],
      status: ProjectStatus.ACTIVE
    };
    this.projects.push(newP);
    this.handleProjectSelected(newP);
  }

  handleProjectSelected(p: Project) {
    this.currentProject = p;
    this.save();
  }

  handleProjectDeleted(p: Project) {
    this.projects = this.projects.filter(proj => proj.id !== p.id);
    if (this.currentProject?.id === p.id) {
      this.currentProject = this.projects[0] || null;
    }
    this.save();
  }

  handleProjectUpdated() {
    this.save();
  }

  // --- Task & Modal Event Handlers ---
  openTaskPopup(task: Task) {
    this.editingTask = { ...task }; // Edit a copy
    this.showPopup = true;
  }

  deleteTask(column: Column, task: Task) {
    debugger
    if (!this.currentProject) return;

    const taskIndex = column.tasks.findIndex(t => t.id === task.id);
    if (taskIndex > -1) {
      column.tasks.splice(taskIndex, 1);
      this.save();
    }
  }

  handleTaskUpdate(updatedTask: Task) {
    if (!this.currentProject) return;

    for (const column of this.currentProject.columns) {
      const taskIndex = column.tasks.findIndex(t => t.id === updatedTask.id);
      if (taskIndex !== -1) {
        column.tasks[taskIndex] = updatedTask;
        break; // Exit after finding and updating
      }
    }
    this.save();
    this.handleModalClosed();
  }

  handleModalClosed() {
    this.editingTask = null;
    this.showPopup = false;
  }


  // --- Misc ---
  toggleTheme() {
    this.isDarkMode = !this.isDarkMode;
    const theme = this.isDarkMode ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('preferred-theme', theme);
  }

  toggleSidebar() {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
  }
}