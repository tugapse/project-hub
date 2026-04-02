import { DragDropModule } from "@angular/cdk/drag-drop";
import { CommonModule } from "@angular/common";
import { Component, EventEmitter, Input, Output } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { TASK_COLORS, TASK_ICONS } from "../../entities/icons-colors";



@Component({
  selector: 'task-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, DragDropModule],
  templateUrl: './modal.html',
  styleUrls: ['./modal.css'],
})
export class TaskModalComponent {

  public readonly TASK_COLORS = TASK_COLORS;
  public readonly TASK_ICONS = TASK_ICONS;


  @Input() editingTask: Task | null = null;
  @Input() showPopup: boolean = false;

  @Output() onUpdate = new EventEmitter<Task>();
  @Output() onClose = new EventEmitter<Task>();

  addChecklistItem(text: string) {
    if (text && this.editingTask) {
      if (!this.editingTask.checklist) {
        this.editingTask.checklist = [];
      }
      this.editingTask.checklist.push({ text, completed: false });
      this.saveTask();
    }
  }

  deleteChecklistItem(index: number) {
    if (this.editingTask && this.editingTask.checklist) {
      this.editingTask.checklist.splice(index, 1);
      this.saveTask();
    }
  }

  getChecklistProgress(task: Task): { completed: number, percentage: number } {
    if (!task.checklist || task.checklist.length === 0) {
      return { completed: 0, percentage: 0 };
    }
    const completed = task.checklist.filter(item => item.completed).length;
    const percentage = (completed / task.checklist.length) * 100;
    return { completed, percentage };
  }

  saveTask() {
    this.onUpdate.emit(this.editingTask!);
  }

  cancelEditingTask() {
    this.onClose.emit();
  }


  updateTask(key: 'color' | 'icon', value: string) {
    if (!this.editingTask) return;
    if (key === 'color') this.editingTask.color = value;
    if (key === 'icon') this.editingTask.icon = value;
    this.saveTask(); // Save changes immediately
  }

  closeTaskPopup() {
    this.onClose.emit();
  }

}
