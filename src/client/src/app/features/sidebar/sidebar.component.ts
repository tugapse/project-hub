import { Component, Input, Output, EventEmitter, HostBinding } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PROJECT_STATUS_LABELS, ProjectStatus, Project, Task, Column } from '../../core/models';
import { ProjectStatusIconComponent } from '../../shared/project-status-icon/project-status-icon.component';
import {
  CdkDragDrop,
  DragDropModule,
  moveItemInArray,
  transferArrayItem,
} from '@angular/cdk/drag-drop';

type SidebarTab = 'active' | 'archived';

interface ProjectGroup {
  status: ProjectStatus;
  /** Section heading; null for the main (unlabelled) group of a tab. */
  label: string | null;
  projects: Project[];
}

/** Which statuses each tab shows, in display order. */
const TAB_STATUSES: Record<SidebarTab, ProjectStatus[]> = {
  active: [ProjectStatus.ACTIVE, ProjectStatus.NOT_STARTED],
  archived: [ProjectStatus.ARCHIVED],
};

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, FormsModule, DragDropModule, ProjectStatusIconComponent],
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
  @Output() projectStatusChanged = new EventEmitter<{ project: Project; status: ProjectStatus }>();

  newProjectName = '';
  editingProject: Project | null = null;
  selectedTab: SidebarTab = 'active';

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

  get groups(): ProjectGroup[] {
    return TAB_STATUSES[this.selectedTab].map((status, index) => ({
      status,
      label: index === 0 ? null : PROJECT_STATUS_LABELS[status],
      projects: this.projects.filter((p) => p.status === status),
    }));
  }

  selectTab(tab: SidebarTab, event: Event) {
    event.preventDefault();
    this.selectedTab = tab;
  }

  /**
   * Reorders projects within a group, or moves one between groups of the same
   * tab (which also changes its status, e.g. Not started -> Active).
   */
  drop(event: CdkDragDrop<Project[]>, targetStatus: ProjectStatus) {
    const groups = this.groups;
    const lists = new Map(groups.map((g) => [g.status, [...g.projects]]));
    const source = lists.get(event.item.data.status as ProjectStatus)!;
    const target = lists.get(targetStatus)!;

    if (source === target) {
      moveItemInArray(target, event.previousIndex, event.currentIndex);
    } else {
      transferArrayItem(source, target, event.previousIndex, event.currentIndex);
    }

    // Visible groups in display order first, then every project from other tabs.
    const visibleStatuses = groups.map((g) => g.status);
    const others = this.projects.filter((p) => !visibleStatuses.includes(p.status));
    const newList = [...visibleStatuses.flatMap((status) => lists.get(status)!), ...others];
    this.projects.splice(0, this.projects.length, ...newList);

    const moved: Project = event.item.data;
    if (moved.status !== targetStatus) {
      this.projectStatusChanged.emit({ project: moved, status: targetStatus });
    } else {
      this.projectUpdated.emit();
    }
  }
}
