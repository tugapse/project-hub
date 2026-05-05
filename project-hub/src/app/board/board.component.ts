import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DragDropModule } from '@angular/cdk/drag-drop';
import {
  CdkDragDrop,
  moveItemInArray,
  transferArrayItem,
} from '@angular/cdk/drag-drop';
import { Project, Column, Task } from '../entities/types';
import { ColumnComponent } from '../column/column.component';

@Component({
  selector: 'app-board',
  standalone: true,
  imports: [CommonModule, DragDropModule, ColumnComponent],
  templateUrl: './board.component.html',
  styleUrls: ['./board.component.css'],
})
export class BoardComponent {
  @Input() currentProject: Project | null = null;

  @Output() taskOpened = new EventEmitter<Task>();
  @Output() taskDeleted = new EventEmitter<{ column: Column; task: Task }>();
  @Output() stateChanged = new EventEmitter<void>(); // New consolidated event

  // --- Event Emitters ---

  openTaskPopup(task: Task) {
    this.taskOpened.emit(task);
  }

  deleteTask(event: { column: Column; task: Task }) {
    this.taskDeleted.emit(event);
  }

  // --- Board Logic ---

  drop(event: CdkDragDrop<Task[]>) {
    if (event.previousContainer === event.container) {
      moveItemInArray(
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );
    } else {
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );
    }
    this.stateChanged.emit();
  }
}