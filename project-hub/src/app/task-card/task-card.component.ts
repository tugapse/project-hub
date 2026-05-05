import {
  Component,
  EventEmitter,
  HostBinding,
  HostListener,
  Input,
  Output,
} from '@angular/core';
import { Column, Task } from '../entities/types';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-task-card',
  templateUrl: './task-card.component.html',
  styleUrls: ['./task-card.component.css'],
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule],
})
export class TaskCardComponent {
  @Input() task!: Task;
  @Input() column!: Column;

  @Output() taskOpened = new EventEmitter<Task>();
  @Output() taskDeleted = new EventEmitter<Task>();

  @HostBinding('class') className = 'task-card';

  @HostBinding('class.task-done')
  get isDone() {
    if (!this.column) {
      return false;
    }
    return this.column.title.toLowerCase() === 'done';
  }

  @HostBinding('style.border-left-color')
  get borderColor() {
    // In the original board.component.html, the color was bound to task.color
    return this.task.color;
  }

  @HostListener('click')
  onClick() {
    this.taskOpened.emit(this.task);
  }

  get truncatedDescription(): string {
    if (!this.task.description) {
      return '';
    }
    if (this.task.description.length <= 80) {
      return this.task.description;
    }
    return this.task.description.slice(0, 80) + '...';
  }

  get checklistProgress() {
    // The original data model uses 'checklist' and items have a 'completed' property.
    if (!this.task.checklist || this.task.checklist.length === 0) {
      return null;
    }
    const completed = this.task.checklist.filter((item) => item.completed).length;
    const total = this.task.checklist.length;
    const percentage = (completed / total) * 100;
    return {
      completed,
      total,
      percentage,
    };
  }

  deleteTask(event: MouseEvent) {
    debugger
    event.stopPropagation();
    this.taskDeleted.emit(this.task);
  }
}