import { Injectable, signal } from '@angular/core';

export interface ConfirmOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  /** Styles the confirm button as a destructive action (default: true). */
  danger?: boolean;
}

interface PendingConfirm extends Required<ConfirmOptions> {
  resolve: (result: boolean) => void;
}

/**
 * Opens a confirmation modal and resolves with the user's choice.
 * The modal itself is rendered by `<app-confirm-dialog>` mounted once in the app root.
 */
@Injectable({ providedIn: 'root' })
export class ConfirmService {
  private readonly _pending = signal<PendingConfirm | null>(null);
  readonly pending = this._pending.asReadonly();

  confirm(options: ConfirmOptions | string): Promise<boolean> {
    const opts = typeof options === 'string' ? { message: options } : options;
    // A new request supersedes any open one, which counts as cancelled.
    this._pending()?.resolve(false);

    return new Promise<boolean>((resolve) => {
      this._pending.set({
        title: 'Are you sure?',
        confirmText: 'Delete',
        cancelText: 'Cancel',
        danger: true,
        ...opts,
        resolve,
      });
    });
  }

  close(result: boolean) {
    const pending = this._pending();
    if (!pending) return;
    this._pending.set(null);
    pending.resolve(result);
  }
}
