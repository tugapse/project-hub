import { Component, Input, Output, EventEmitter } from '@angular/core';
import { Project } from '../entities/types';
import { CommonModule } from '@angular/common';

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
  @Output() themeToggled = new EventEmitter<void>();

  onToggleTheme() {
    this.themeToggled.emit();
  }
}