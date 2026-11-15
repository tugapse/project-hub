import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PROJECT_STATUS_LABELS, Project, ProjectStatus, SyncState } from '../../core/models';
import { ProjectStatusIconComponent } from '../../shared/project-status-icon/project-status-icon.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, ProjectStatusIconComponent],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css'],
})
export class HeaderComponent {
  @Input() currentProject: Project | null = null;
  @Input() syncState: SyncState | null = null;
  @Input() isDarkMode = false;
  @Output() themeToggled = new EventEmitter<void>();
  @Output() statusChanged = new EventEmitter<ProjectStatus>();

  readonly statuses = [ProjectStatus.NOT_STARTED, ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED];
  readonly statusLabels = PROJECT_STATUS_LABELS;

  onToggleTheme() {
    this.themeToggled.emit();
  }
}
