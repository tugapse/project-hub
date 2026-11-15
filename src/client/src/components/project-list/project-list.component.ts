import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Project, Column } from '../../entities/interfaces';

@Component({
  selector: 'app-project-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './project-list.component.html'
})
export class ProjectListComponent implements OnChanges {
  @Input() projects: Project[] = [];
  @Input() currentProject: Project | null = null;
  @Output() onProjectSelected = new EventEmitter<Project>();
  @Output() onProjectAdded = new EventEmitter<string>();
  @Output() onProjectDeleted = new EventEmitter<Project>();
  @Output() onProjectUpdated = new EventEmitter<void>();

  startedProjects: Project[] = [];
  notStartedProjects: Project[] = [];
  editingProjectId: string | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['projects']) {
      this.classifyProjects();
    }
  }

  private classifyProjects() {
    this.startedProjects = this.projects.filter(p => !this.isNotStarted(p));
    this.notStartedProjects = this.projects.filter(p => this.isNotStarted(p));
  }

  private isNotStarted(project: Project): boolean {
    console.log('Classifying project:', project.name, 'Columns:', JSON.stringify(project.columns.map(c => ({id: c.id, title: c.title, task_count: c.tasks.length}))));
    const todo = project.columns.find((c: Column) => c.id === 'todo')?.tasks.length || 0;
    const doing = project.columns.find((c: Column) => c.id === 'doing')?.tasks.length || 0;
    const done = project.columns.find((c: Column) => c.id === 'done')?.tasks.length || 0;
    return todo > 0 && doing === 0 && done === 0;
  }

  selectProject(project: Project) {
    this.onProjectSelected.emit(project);
  }

  addProject(name: string) {
    this.onProjectAdded.emit(name);
  }

  deleteProject(project: Project, event: MouseEvent) {
    event.stopPropagation();
    this.onProjectDeleted.emit(project);
  }

  startEditingProject(project: Project) {
    this.editingProjectId = project.id;
    setTimeout(() => {
      const el = document.querySelector('.proj-edit-input') as HTMLInputElement;
      el?.focus();
    }, 50);
  }

  stopEditingProject() {
    this.editingProjectId = null;
    this.onProjectUpdated.emit();
  }

  getProjectProgress(project: Project) {
    const todo = project.columns.find((c: Column) => c.id === 'todo')?.tasks.length || 0;
    const doing = project.columns.find((c: Column) => c.id === 'doing')?.tasks.length || 0;
    const done = project.columns.find((c: Column) => c.id === 'done')?.tasks.length || 0;
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
}