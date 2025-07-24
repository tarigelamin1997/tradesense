// Accessibility utilities for keyboard navigation and screen readers

import { browser } from '$app/environment';

// Announce messages to screen readers
export function announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
  if (!browser) return;
  
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.style.width = '1px';
  announcement.style.height = '1px';
  announcement.style.overflow = 'hidden';
  
  announcement.textContent = message;
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

// Trap focus within a container (for modals, dialogs)
export function trapFocus(container: HTMLElement) {
  const focusableElements = container.querySelectorAll(
    'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstFocusable = focusableElements[0] as HTMLElement;
  const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement;
  
  function handleKeyDown(e: KeyboardEvent) {
    if (e.key !== 'Tab') return;
    
    if (e.shiftKey) {
      if (document.activeElement === firstFocusable) {
        lastFocusable.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastFocusable) {
        firstFocusable.focus();
        e.preventDefault();
      }
    }
  }
  
  container.addEventListener('keydown', handleKeyDown);
  firstFocusable?.focus();
  
  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
}

// Manage focus for route changes
export function manageFocus(selector: string = 'main h1, main h2, [role="main"] h1') {
  if (!browser) return;
  
  // Wait for DOM update
  setTimeout(() => {
    const element = document.querySelector(selector) as HTMLElement;
    if (element) {
      // Make temporarily focusable
      const originalTabIndex = element.getAttribute('tabindex');
      element.setAttribute('tabindex', '-1');
      element.focus();
      
      // Restore original tabindex
      if (originalTabIndex) {
        element.setAttribute('tabindex', originalTabIndex);
      } else {
        element.removeAttribute('tabindex');
      }
    }
  }, 100);
}

// Keyboard navigation handler
export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
}

export class KeyboardNavigationManager {
  private shortcuts: Map<string, KeyboardShortcut> = new Map();
  private enabled = true;
  
  constructor() {
    if (browser) {
      document.addEventListener('keydown', this.handleKeyDown.bind(this));
    }
  }
  
  private handleKeyDown(e: KeyboardEvent) {
    if (!this.enabled) return;
    
    // Skip if user is typing in an input
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return;
    }
    
    const shortcutKey = this.getShortcutKey(e);
    const shortcut = this.shortcuts.get(shortcutKey);
    
    if (shortcut) {
      e.preventDefault();
      shortcut.action();
    }
  }
  
  private getShortcutKey(e: KeyboardEvent): string {
    const parts = [];
    if (e.ctrlKey || e.metaKey) parts.push('ctrl');
    if (e.shiftKey) parts.push('shift');
    if (e.altKey) parts.push('alt');
    parts.push(e.key.toLowerCase());
    return parts.join('+');
  }
  
  register(shortcut: KeyboardShortcut) {
    const key = this.getShortcutKeyFromConfig(shortcut);
    this.shortcuts.set(key, shortcut);
  }
  
  private getShortcutKeyFromConfig(shortcut: KeyboardShortcut): string {
    const parts = [];
    if (shortcut.ctrl) parts.push('ctrl');
    if (shortcut.shift) parts.push('shift');
    if (shortcut.alt) parts.push('alt');
    parts.push(shortcut.key.toLowerCase());
    return parts.join('+');
  }
  
  unregister(shortcut: KeyboardShortcut) {
    const key = this.getShortcutKeyFromConfig(shortcut);
    this.shortcuts.delete(key);
  }
  
  disable() {
    this.enabled = false;
  }
  
  enable() {
    this.enabled = true;
  }
  
  getShortcuts(): KeyboardShortcut[] {
    return Array.from(this.shortcuts.values());
  }
  
  destroy() {
    if (browser) {
      document.removeEventListener('keydown', this.handleKeyDown.bind(this));
    }
    this.shortcuts.clear();
  }
}

// Create global instance
export const keyboardNav = new KeyboardNavigationManager();

// Common keyboard shortcuts
export function registerCommonShortcuts() {
  // Navigation shortcuts
  keyboardNav.register({
    key: 'g',
    action: () => {
      const input = document.querySelector('[data-global-search]') as HTMLInputElement;
      input?.focus();
    },
    description: 'Focus global search'
  });
  
  keyboardNav.register({
    key: '/',
    action: () => {
      const input = document.querySelector('[data-global-search]') as HTMLInputElement;
      input?.focus();
    },
    description: 'Focus global search'
  });
  
  keyboardNav.register({
    key: '?',
    shift: true,
    action: () => {
      announce('Keyboard shortcuts: Press G for search, Escape to close dialogs');
    },
    description: 'Show keyboard shortcuts'
  });
}

// Skip navigation component props
export interface SkipLink {
  href: string;
  text: string;
}

export const defaultSkipLinks: SkipLink[] = [
  { href: '#main-content', text: 'Skip to main content' },
  { href: '#main-navigation', text: 'Skip to navigation' },
  { href: '#search', text: 'Skip to search' }
];

// Focus visible utility
export function ensureFocusVisible() {
  if (!browser) return;
  
  // Add focus-visible polyfill styles
  const style = document.createElement('style');
  style.textContent = `
    /* Focus styles for keyboard navigation */
    :focus {
      outline: 2px solid transparent;
    }
    
    :focus-visible {
      outline: 2px solid #10b981;
      outline-offset: 2px;
    }
    
    /* Ensure focus is visible in dark mode */
    .dark :focus-visible {
      outline-color: #34d399;
    }
    
    /* Skip links */
    .skip-links {
      position: absolute;
      top: -40px;
      left: 0;
      z-index: 9999;
    }
    
    .skip-links:focus-within {
      top: 0;
    }
    
    .skip-links a {
      position: absolute;
      left: -10000px;
      top: auto;
      width: 1px;
      height: 1px;
      overflow: hidden;
      background: #10b981;
      color: white;
      padding: 0.5rem 1rem;
      text-decoration: none;
      border-radius: 0.25rem;
    }
    
    .skip-links a:focus {
      position: static;
      width: auto;
      height: auto;
    }
  `;
  
  document.head.appendChild(style);
}

// ARIA live region manager
export class LiveRegionManager {
  private region: HTMLElement | null = null;
  
  constructor() {
    if (browser) {
      this.createRegion();
    }
  }
  
  private createRegion() {
    this.region = document.createElement('div');
    this.region.setAttribute('aria-live', 'polite');
    this.region.setAttribute('aria-atomic', 'true');
    this.region.className = 'sr-only';
    this.region.style.position = 'absolute';
    this.region.style.left = '-10000px';
    this.region.style.width = '1px';
    this.region.style.height = '1px';
    this.region.style.overflow = 'hidden';
    document.body.appendChild(this.region);
  }
  
  announce(message: string) {
    if (!this.region) return;
    this.region.textContent = message;
    
    // Clear after announcement
    setTimeout(() => {
      if (this.region) {
        this.region.textContent = '';
      }
    }, 1000);
  }
  
  destroy() {
    if (this.region && this.region.parentNode) {
      this.region.parentNode.removeChild(this.region);
    }
  }
}

// Color contrast checker
export function checkColorContrast(foreground: string, background: string): number {
  // Convert hex to RGB
  const getRGB = (color: string) => {
    const hex = color.replace('#', '');
    return {
      r: parseInt(hex.substr(0, 2), 16),
      g: parseInt(hex.substr(2, 2), 16),
      b: parseInt(hex.substr(4, 2), 16)
    };
  };
  
  // Calculate relative luminance
  const getLuminance = (rgb: { r: number; g: number; b: number }) => {
    const { r, g, b } = rgb;
    const sRGB = [r, g, b].map(val => {
      val = val / 255;
      return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * sRGB[0] + 0.7152 * sRGB[1] + 0.0722 * sRGB[2];
  };
  
  const fg = getRGB(foreground);
  const bg = getRGB(background);
  
  const l1 = getLuminance(fg);
  const l2 = getLuminance(bg);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

// Check if contrast meets WCAG standards
export function meetsWCAGContrast(
  contrast: number,
  level: 'AA' | 'AAA' = 'AA',
  fontSize: 'normal' | 'large' = 'normal'
): boolean {
  if (level === 'AA') {
    return fontSize === 'large' ? contrast >= 3 : contrast >= 4.5;
  } else {
    return fontSize === 'large' ? contrast >= 4.5 : contrast >= 7;
  }
}