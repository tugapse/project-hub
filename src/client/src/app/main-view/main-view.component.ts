import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../header/header.component';
import { BoardComponent } from '../board/board.component';

import { SyncState } from '../entities/types';
import { ProjectStatus } from '../../entities/enums';
import { Project, Task, Column } from '../../entities/interfaces';

@Component({
  selector: 'app-main-view',
  standalone: true,
  imports: [CommonModule, HeaderComponent, BoardComponent],
  templateUrl: './main-view.component.html',
  styleUrls: ['./main-view.component.css']
})
export class MainViewComponent {
  @Input() currentProject: Project | null = null;
  @Input() syncState: SyncState = 'synced';
  @Input() isDarkMode = false;

  @Output() stateChanged = new EventEmitter<void>();
  @Output() taskOpened = new EventEmitter<Task>();
  @Output() taskDeleted = new EventEmitter<{ column: Column, task: Task }>();
  @Output() themeToggled = new EventEmitter<void>();
  @Output() projectStateToggled = new EventEmitter<void>();

  get isProjectArchived(): boolean {
    return this.currentProject?.status === ProjectStatus.ARCHIVED;
  }

  onToggleTheme(): void {
    this.themeToggled.emit();
  }

  onToggleProjectState(): void {
    if (this.currentProject) {
      this.currentProject.status =
        this.currentProject.status === ProjectStatus.ARCHIVED
          ? ProjectStatus.ACTIVE
          : ProjectStatus.ARCHIVED;
      this.onStateChanged();
    }
  }

  onStateChanged(): void {
    this.stateChanged.emit();
  }

  onTaskOpened(task: Task): void {
    this.taskOpened.emit(task);
  }

  onTaskDeleted(event: { column: Column, task: Task }): void {
    this.taskDeleted.emit(event);
  }
}