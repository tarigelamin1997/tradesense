/**
 * Feedback context capture utilities
 * Tracks user journey, actions, and errors for better bug reports
 */

interface UserAction {
  type: string;
  target?: string;
  timestamp: Date;
  data?: any;
}

interface ErrorLog {
  message: string;
  stack?: string;
  timestamp: Date;
  url: string;
}

class FeedbackContextManager {
  private static instance: FeedbackContextManager;
  private previousPages: string[] = [];
  private lastActions: UserAction[] = [];
  private errorLogs: ErrorLog[] = [];
  private maxItems = 10;

  private constructor() {
    this.setupListeners();
    this.loadFromSession();
  }

  static getInstance(): FeedbackContextManager {
    if (!FeedbackContextManager.instance) {
      FeedbackContextManager.instance = new FeedbackContextManager();
    }
    return FeedbackContextManager.instance;
  }

  private setupListeners() {
    // Track page navigation
    if (typeof window !== 'undefined') {
      // Track errors
      window.addEventListener('error', (event) => {
        this.logError({
          message: event.message,
          stack: event.error?.stack,
          timestamp: new Date(),
          url: window.location.pathname
        });
      });

      // Track unhandled promise rejections
      window.addEventListener('unhandledrejection', (event) => {
        this.logError({
          message: `Unhandled Promise: ${event.reason}`,
          timestamp: new Date(),
          url: window.location.pathname
        });
      });

      // Track user clicks
      document.addEventListener('click', (event) => {
        const target = event.target as HTMLElement;
        const identifier = target.id || target.className || target.tagName;
        this.logAction({
          type: 'click',
          target: identifier,
          timestamp: new Date()
        });
      });

      // Track form submissions
      document.addEventListener('submit', (event) => {
        const form = event.target as HTMLFormElement;
        this.logAction({
          type: 'form_submit',
          target: form.id || form.name || 'unnamed_form',
          timestamp: new Date()
        });
      });

      // Save to session storage periodically
      setInterval(() => this.saveToSession(), 5000);
    }
  }

  addPageVisit(url: string) {
    this.previousPages.unshift(url);
    if (this.previousPages.length > this.maxItems) {
      this.previousPages.pop();
    }
    this.saveToSession();
  }

  logAction(action: UserAction) {
    this.lastActions.unshift(action);
    if (this.lastActions.length > this.maxItems) {
      this.lastActions.pop();
    }
  }

  logError(error: ErrorLog) {
    this.errorLogs.unshift(error);
    if (this.errorLogs.length > this.maxItems) {
      this.errorLogs.pop();
    }
  }

  getContext() {
    return {
      previousPages: [...this.previousPages],
      lastActions: [...this.lastActions],
      errorLogs: [...this.errorLogs],
      browser: this.getBrowserInfo()
    };
  }

  private getBrowserInfo(): string {
    const ua = navigator.userAgent;
    if (ua.includes('Chrome')) return 'Chrome';
    if (ua.includes('Firefox')) return 'Firefox';
    if (ua.includes('Safari')) return 'Safari';
    if (ua.includes('Edge')) return 'Edge';
    return 'Unknown';
  }

  private saveToSession() {
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem('feedback_context', JSON.stringify({
        previousPages: this.previousPages,
        lastActions: this.lastActions,
        errorLogs: this.errorLogs
      }));
    }
  }

  private loadFromSession() {
    if (typeof sessionStorage !== 'undefined') {
      const saved = sessionStorage.getItem('feedback_context');
      if (saved) {
        try {
          const data = JSON.parse(saved);
          this.previousPages = data.previousPages || [];
          this.lastActions = data.lastActions || [];
          this.errorLogs = data.errorLogs || [];
        } catch (e) {
          console.error('Failed to load feedback context:', e);
        }
      }
    }
  }

  clear() {
    this.previousPages = [];
    this.lastActions = [];
    this.errorLogs = [];
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.removeItem('feedback_context');
    }
  }
}

// Export singleton instance
export const feedbackContext = typeof window !== 'undefined' 
  ? FeedbackContextManager.getInstance() 
  : null;

// Export capture function
export function capturePageContext() {
  return feedbackContext?.getContext() || {
    previousPages: [],
    lastActions: [],
    errorLogs: [],
    browser: 'Unknown'
  };
}

// Hook for SvelteKit page changes
export function trackPageVisit(url: string) {
  feedbackContext?.addPageVisit(url);
}

// Manual action tracking
export function trackAction(type: string, data?: any) {
  feedbackContext?.logAction({
    type,
    timestamp: new Date(),
    data
  });
}