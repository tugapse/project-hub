import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Project } from '../../entities/interfaces';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent {
  @Input() currentProject: Project | null = null;
  @Input() isSyncing = false;
  @Input() isDarkMode = false;
  @Input() isProjectArchived = false;
  @Output() themeToggled = new EventEmitter<void>();
  @Output() projectStateToggled = new EventEmitter<void>();

  onToggleTheme() {
    this.themeToggled.emit();
  }

  onToggleProjectState() {
    this.projectStateToggled.emit();
  }
}