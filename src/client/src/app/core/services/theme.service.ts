import { Injectable, signal } from '@angular/core';

type Theme = 'light' | 'dark';
const STORAGE_KEY = 'preferred-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly isDarkMode = signal(false);

  init() {
    this.apply((localStorage.getItem(STORAGE_KEY) as Theme) || 'light');
  }

  toggle() {
    const theme: Theme = this.isDarkMode() ? 'light' : 'dark';
    this.apply(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }

  private apply(theme: Theme) {
    this.isDarkMode.set(theme === 'dark');
    document.documentElement.setAttribute('data-theme', theme);
  }
}
