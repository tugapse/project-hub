import { Component, Input, Output, EventEmitter, HostBinding } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ProjectStatus } from '../../entities/enums';
import { Project, Task, Column } from '../../entities/interfaces';
import {
  CdkDragDrop,
  DragDropModule,
  moveItemInArray,
} from '@angular/cdk/drag-drop';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [ CommonModule, FormsModule, DragDropModule ],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  @Input() projects: Project[] = [];
  @Input() currentProject: Project | null = null;
  @Input() isCollapsed = false;

  @Output() projectSelected = new EventEmitter<Project>();
  @Output() projectAdded = new EventEmitter<string>();
  @Output() projectDeleted = new EventEmitter<Project>();
  @Output() projectUpdated = new EventEmitter<void>();

  newProjectName = '';
  editingProject: Project | null = null;
  _ProjectStatus = ProjectStatus;
  selectedProjectStatus: ProjectStatus = ProjectStatus.ACTIVE;

  




  @HostBinding('class.collapsed')
  get isDone() {
   return this.isCollapsed
  }

  calculateProgress(project: Project): { [key: string]: number } {
    const allTasks: Task[] = project.columns.flatMap((column: Column) => column.tasks);
    const totalTasks = allTasks.length;

    if (totalTasks === 0) {
      return { todo: 0, doing: 0, done: 0 };
    }

    const tasksByStatus = project.columns.reduce((acc, column) => {
      acc[column.id] = (acc[column.id] || 0) + column.tasks.length;
      return acc;
    }, {} as { [key: string]: number });

    return {
      todo: ((tasksByStatus['todo'] || 0) / totalTasks) * 100,
      doing: ((tasksByStatus['doing'] || 0) / totalTasks) * 100,
      done: ((tasksByStatus['done'] || 0) / totalTasks) * 100,
    };
  }

  selectProject(project: Project) {
    this.projectSelected.emit(project);
  }

  addProject() {
    if (this.newProjectName.trim()) {
      this.projectAdded.emit(this.newProjectName.trim());
      this.newProjectName = '';
    }
  }

  updateProject() {
    this.projectUpdated.emit();
  }

  deleteProject(project: Project, event: MouseEvent) {
    event.stopPropagation(); // Prevent selectProject from being called
    if (confirm(`Are you sure you want to delete project "${project.name}"?`)) {
      this.projectDeleted.emit(project);
    }
  }

  startEditing(project: Project, event: MouseEvent) {
    event.stopPropagation();
    this.editingProject = { ...project }; // Edit a copy
  }

  finishEditing(project: Project, newName: string) {
    if (this.editingProject && newName.trim() && newName.trim() !== project.name) {
      project.name = newName.trim();
      this.projectUpdated.emit();
    }
    this.editingProject = null;
  }

  cancelEditing() {
    this.editingProject = null;
  }

  get displayedProjects(): Project[] {
    return this.projects.filter(p => p.status === this.selectedProjectStatus);
  }

  drop(event: CdkDragDrop<Project[]>) {
    // Create a mutable copy of the displayed projects array
    const reorderedDisplayedList = [...this.displayedProjects];
    
    // Apply the move to the copy
    moveItemInArray(reorderedDisplayedList, event.previousIndex, event.currentIndex);

    // Get all projects that are not in the current filtered view
    const otherProjects = this.projects.filter(p => p.status !== this.selectedProjectStatus);
    
    // Reconstruct the full list: the reordered part first, then the rest
    const newList = [...reorderedDisplayedList, ...otherProjects];

    // Update the original projects array in-place to maintain the object reference
    this.projects.splice(0, this.projects.length, ...newList);

    // Emit event to notify parent component to persist the changes
    this.projectUpdated.emit();
  }
}