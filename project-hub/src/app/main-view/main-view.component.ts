import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Project, Task, Column } from '../entities/types';
import { HeaderComponent } from '../header/header.component';
import { BoardComponent } from '../board/board.component';

@Component({
  selector: 'app-main-view',
  standalone: true,
  imports: [CommonModule, HeaderComponent, BoardComponent],
  templateUrl: './main-view.component.html',
  styleUrls: ['./main-view.component.css']
})
export class MainViewComponent {
  @Input() currentProject: Project | null = null;
  @Input() isSyncing = false;
  @Input() isDarkMode = false;

  @Output() stateChanged = new EventEmitter<void>();
  @Output() taskOpened = new EventEmitter<Task>();
  @Output() taskDeleted = new EventEmitter<{ column: Column, task: Task }>();
  @Output() themeToggled = new EventEmitter<void>();

  // These methods will be called by the template and will emit the events.
  onToggleTheme(): void {
    this.themeToggled.emit();
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