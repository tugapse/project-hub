import { Component, EventEmitter, Input, Output } from '@angular/core';
import { HeaderComponent } from '../header/header.component';
import { BoardComponent } from '../board/board.component';
import { Column, Project, ProjectStatus, SyncState, Task } from '../../core/models';

@Component({
  selector: 'app-main-view',
  standalone: true,
  imports: [HeaderComponent, BoardComponent],
  templateUrl: './main-view.component.html',
  styleUrls: ['./main-view.component.css'],
})
export class MainViewComponent {
  @Input() currentProject: Project | null = null;
  @Input() syncState: SyncState = 'synced';
  @Input() isDarkMode = false;

  /** Tasks were added or moved on the board. */
  @Output() boardChanged = new EventEmitter<void>();
  @Output() statusChanged = new EventEmitter<ProjectStatus>();
  @Output() taskOpened = new EventEmitter<Task>();
  @Output() taskDeleted = new EventEmitter<{ column: Column; task: Task }>();
  @Output() themeToggled = new EventEmitter<void>();
}
