import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DragDropModule, CdkDropList, CdkDragDrop } from '@angular/cdk/drag-drop';
import { TaskCardComponent } from '../task-card/task-card.component';
import { Column, Task } from '../../entities/interfaces';

@Component({
  selector: 'app-column',
  standalone: true,
  imports: [CommonModule, DragDropModule, TaskCardComponent],
  templateUrl: './column.component.html',
  styleUrls: ['./column.component.css'],
})
export class ColumnComponent {
  @Input() column: Column | null = null;
  @Input() cdkDropListConnectedTo: CdkDropList[] = [];

  @Output() taskOpened = new EventEmitter<Task>();
  @Output() taskDeleted = new EventEmitter<{ column: Column; task: Task }>();
  @Output() stateChanged = new EventEmitter<void>();
  @Output() cdkDropListDropped = new EventEmitter<CdkDragDrop<Task[]>>();

  openTaskPopup(task: Task) {
    this.taskOpened.emit(task);
  }

  deleteTask(task: Task) {
    debugger
    if (this.column) {
      this.taskDeleted.emit({ column: this.column, task });
    }
  }

  addTask(inputElement: HTMLInputElement) {
    const content = inputElement.value;
    if (content.trim() && this.column) {
      this.column.tasks.push({
        id: Date.now(),
        content,
        description: '',
        color: '#475569',
        icon: '',
        checklistTitle: 'Todos :',
        checklist: [],
        notes: '',
      });
      inputElement.value = '';
      this.stateChanged.emit();
    }
  }
}