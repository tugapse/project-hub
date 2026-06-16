# Task: Implement Project State Toggle Functionality

## Objective

The goal is to add a toggle button to the header of the `project-hub` application. This button will allow the user to toggle the state of the currently viewed project between "active" and "archived".

This involves updating the front-end components to display the button and emit an event, and then handling that event in the main application component to modify the project's state.

---

## Step-by-Step Instructions

### 1. Modify the Header Component Logic

Update the header component's TypeScript file to accept the project's archived status and to emit an event when the state is toggled.

**File:** `project-hub/src/app/header/header.component.ts`

**Action:** Replace the entire content of the file with the following code.

```typescript
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
```

### 2. Modify the Header Component Template

Add the toggle button to the header's HTML. The button's text will change depending on the project's state.

**File:** `project-hub/src/app/header/header.component.html`

**Action:** Replace the entire content of the file with the following code.

```html
<header>
  <div class="header-left">
    <ng-container *ngIf="currentProject">
      <h1>{{ currentProject.name }}</h1>
    </ng-container>
    <div class="status-pill" [class.syncing]="isSyncing">
      <span class="dot"></span>
      {{ isSyncing ? 'Syncing...' : 'System Synced' }}
    </div>
  </div>
  <div class="header-right">
    <button (click)="onToggleProjectState()" class="state-toggle">
      {{ isProjectArchived ? 'Unarchive' : 'Archive' }}
    </button>
    <button (click)="onToggleTheme()" class="theme-toggle">
      {{ isDarkMode ? ' Light' : ' Dark' }}
    </button>
  </div>
</header>
```

### 3. Connect the Header in the Main View Template

Update the `main-view` component's template to pass the project's archived status to the header and to listen for the toggle event.

**File:** `project-hub/src/app/main-view/main-view.component.html`

**Action:** Replace the entire content of the file with the following code.

```html
<main class="board-container">
  <app-header
    *ngIf="currentProject"
    [currentProject]="currentProject"
    [isSyncing]="isSyncing"
    [isDarkMode]="isDarkMode"
    [isProjectArchived]="currentProject.archived"
    (themeToggled)="onToggleTheme()"
    (projectStateToggled)="onToggleProjectState()"
  ></app-header>

  <app-board
    *ngIf="currentProject"
    [currentProject]="currentProject"
    (stateChanged)="onStateChanged()"
    (taskOpened)="onTaskOpened($event)"
    (taskDeleted)="onTaskDeleted($event)"
  ></app-board>
</main>
```

### 4. Propagate the Event Through the Main View Logic

Update the `main-view` component's TypeScript file to bubble the `projectStateToggled` event up to its parent.

**File:** `project-hub/src/app/main-view/main-view.component.ts`

**Action:** Replace the entire content of the file with the following code.

```typescript
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../header/header.component';
import { BoardComponent } from '../board/board.component';
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
  @Input() isSyncing = false;
  @Input() isDarkMode = false;

  @Output() stateChanged = new EventEmitter<void>();
  @Output() taskOpened = new EventEmitter<Task>();
  @Output() taskDeleted = new EventEmitter<{ column: Column, task: Task }>();
  @Output() themeToggled = new EventEmitter<void>();
  @Output() projectStateToggled = new EventEmitter<void>();

  onToggleTheme(): void {
    this.themeToggled.emit();
  }

  onToggleProjectState(): void {
    this.projectStateToggled.emit();
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
```

### 5. Final Implementation in the Root App Component

The final step is to handle the event in the main application component (`app.ts`), which manages the application's overall state.

**File:** `project-hub/src/app/app.ts`

**Action:**
1.  Find where the `<app-main-view>` component is used in `app.html` (or the equivalent template file).
2.  Listen for the `(projectStateToggled)` event and bind it to a new method in `app.ts`, e.g., `handleProjectStateToggle()`.
3.  Implement the `handleProjectStateToggle()` method. Inside this method, you will:
    *   Check if `this.currentProject` is not null.
    *   Invert its `archived` property: `this.currentProject.archived = !this.currentProject.archived;`
    *   Call the existing method responsible for saving the project state to the backend/local storage (e.g., `saveProjects()` or similar).
