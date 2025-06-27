/**
 * Accessibility utility functions
 */

/**
 * Manages focus trap within a container element
 */
export const useFocusTrap = (containerRef: React.RefObject<HTMLElement>) => {
  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    return () => container.removeEventListener('keydown', handleTabKey);
  }, [containerRef]);
};

/**
 * Announces messages to screen readers
 */
export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Checks if an element is keyboard focusable
 */
export const isFocusable = (element: HTMLElement): boolean => {
  if (element.tabIndex < 0) return false;
  if (element.hasAttribute('disabled')) return false;
  if (element.style.display === 'none') return false;
  if (element.style.visibility === 'hidden') return false;

  return true;
};

/**
 * Gets the accessible name of an element
 */
export const getAccessibleName = (element: HTMLElement): string => {
  // Check aria-label first
  const ariaLabel = element.getAttribute('aria-label');
  if (ariaLabel) return ariaLabel;

  // Check aria-labelledby
  const labelledBy = element.getAttribute('aria-labelledby');
  if (labelledBy) {
    const labelElement = document.getElementById(labelledBy);
    if (labelElement) return labelElement.textContent || '';
  }

  // Check associated label for form controls
  if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
    const label = document.querySelector(`label[for="${element.id}"]`);
    if (label) return label.textContent || '';
  }

  // Fall back to text content
  return element.textContent || '';
};

/**
 * Validates color contrast ratio
 */
export const getContrastRatio = (color1: string, color2: string): number => {
  // This is a simplified implementation
  // In production, you'd want to use a proper color contrast library
  const getLuminance = (color: string): number => {
    // Convert hex to RGB and calculate relative luminance
    // Simplified calculation for demo purposes
    return 0.5; // Placeholder
  };

  const l1 = getLuminance(color1);
  const l2 = getLuminance(color2);

  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
};

/**
 * Checks if contrast ratio meets WCAG standards
 */
export const meetsContrastRequirement = (
  ratio: number, 
  level: 'AA' | 'AAA' = 'AA',
  textSize: 'normal' | 'large' = 'normal'
): boolean => {
  const requirements = {
    AA: { normal: 4.5, large: 3 },
    AAA: { normal: 7, large: 4.5 }
  };

  return ratio >= requirements[level][textSize];
};
/**
 * Accessibility utilities for TradeSense
 */

// Focus management
export const focusManagement = {
  /**
   * Trap focus within a container (useful for modals)
   */
  trapFocus: (containerElement: HTMLElement) => {
    const focusableElements = containerElement.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }

      if (e.key === 'Escape') {
        containerElement.dispatchEvent(new CustomEvent('escape'));
      }
    };

    containerElement.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => {
      containerElement.removeEventListener('keydown', handleTabKey);
    };
  },

  /**
   * Restore focus to previously focused element
   */
  restoreFocus: (previousElement: HTMLElement | null) => {
    if (previousElement && document.contains(previousElement)) {
      previousElement.focus();
    }
  },
};

// ARIA announcements
export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.style.width = '1px';
  announcement.style.height = '1px';
  announcement.style.overflow = 'hidden';

  document.body.appendChild(announcement);
  announcement.textContent = message;

  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

// Keyboard navigation helpers
export const keyboardNavigation = {
  /**
   * Handle arrow key navigation for lists/grids
   */
  handleArrowNavigation: (
    event: KeyboardEvent,
    currentIndex: number,
    itemCount: number,
    onNavigate: (newIndex: number) => void,
    orientation: 'horizontal' | 'vertical' = 'vertical'
  ) => {
    let newIndex = currentIndex;

    switch (event.key) {
      case 'ArrowUp':
        if (orientation === 'vertical') {
          newIndex = currentIndex > 0 ? currentIndex - 1 : itemCount - 1;
          event.preventDefault();
        }
        break;
      case 'ArrowDown':
        if (orientation === 'vertical') {
          newIndex = currentIndex < itemCount - 1 ? currentIndex + 1 : 0;
          event.preventDefault();
        }
        break;
      case 'ArrowLeft':
        if (orientation === 'horizontal') {
          newIndex = currentIndex > 0 ? currentIndex - 1 : itemCount - 1;
          event.preventDefault();
        }
        break;
      case 'ArrowRight':
        if (orientation === 'horizontal') {
          newIndex = currentIndex < itemCount - 1 ? currentIndex + 1 : 0;
          event.preventDefault();
        }
        break;
      case 'Home':
        newIndex = 0;
        event.preventDefault();
        break;
      case 'End':
        newIndex = itemCount - 1;
        event.preventDefault();
        break;
    }

    if (newIndex !== currentIndex) {
      onNavigate(newIndex);
    }
  },

  /**
   * Create roving tabindex for navigation
   */
  createRovingTabIndex: (items: HTMLElement[], activeIndex: number = 0) => {
    items.forEach((item, index) => {
      item.setAttribute('tabindex', index === activeIndex ? '0' : '-1');
    });

    return (newActiveIndex: number) => {
      items.forEach((item, index) => {
        item.setAttribute('tabindex', index === newActiveIndex ? '0' : '-1');
      });
      items[newActiveIndex]?.focus();
    };
  },
};

// ARIA attribute helpers
export const ariaHelpers = {
  /**
   * Generate unique IDs for ARIA relationships
   */
  generateId: (prefix: string = 'aria'): string => {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  },

  /**
   * Create ARIA describedby relationships
   */
  createDescribedBy: (controlId: string, descriptionId: string, element: HTMLElement) => {
    const existingDescribedBy = element.getAttribute('aria-describedby');
    const newDescribedBy = existingDescribedBy
      ? `${existingDescribedBy} ${descriptionId}`
      : descriptionId;

    element.setAttribute('aria-describedby', newDescribedBy);

    return () => {
      const currentDescribedBy = element.getAttribute('aria-describedby');
      if (currentDescribedBy) {
        const updated = currentDescribedBy
          .split(' ')
          .filter(id => id !== descriptionId)
          .join(' ');

        if (updated) {
          element.setAttribute('aria-describedby', updated);
        } else {
          element.removeAttribute('aria-describedby');
        }
      }
    };
  },

  /**
   * Set ARIA expanded state
   */
  setExpanded: (element: HTMLElement, expanded: boolean) => {
    element.setAttribute('aria-expanded', expanded.toString());
  },

  /**
   * Set ARIA selected state
   */
  setSelected: (element: HTMLElement, selected: boolean) => {
    element.setAttribute('aria-selected', selected.toString());
  },
};

// Color contrast and visual helpers
export const visualHelpers = {
  /**
   * Check if user prefers reduced motion
   */
  prefersReducedMotion: (): boolean => {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  },

  /**
   * Check if user prefers high contrast
   */
  prefersHighContrast: (): boolean => {
    return window.matchMedia('(prefers-contrast: high)').matches;
  },

  /**
   * Get appropriate animation duration based on user preferences
   */
  getAnimationDuration: (defaultDuration: number): number => {
    return visualHelpers.prefersReducedMotion() ? 0 : defaultDuration;
  },

  /**
   * Check color contrast ratio (simplified)
   */
  hasGoodContrast: (foreground: string, background: string): boolean => {
    // This is a simplified version - in production, use a proper color contrast library
    // Return true for now, but implement proper contrast checking
    return true;
  },
};

// Touch and mobile helpers
export const touchHelpers = {
  /**
   * Check if device supports touch
   */
  isTouchDevice: (): boolean => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  },

  /**
   * Get appropriate touch target size
   */
  getTouchTargetSize: (): number => {
    return touchHelpers.isTouchDevice() ? 44 : 32; // 44px for touch, 32px for mouse
  },

  /**
   * Handle both click and touch events
   */
  handleActivation: (
    element: HTMLElement,
    callback: () => void,
    options: { preventDefault?: boolean } = {}
  ) => {
    const handleEvent = (event: Event) => {
      if (options.preventDefault) {
        event.preventDefault();
      }
      callback();
    };

    element.addEventListener('click', handleEvent);
    element.addEventListener('touchend', handleEvent);

    return () => {
      element.removeEventListener('click', handleEvent);
      element.removeEventListener('touchend', handleEvent);
    };
  },
};

// Form accessibility helpers
export const formHelpers = {
  /**
   * Associate form control with its label and error message
   */
  associateFormControl: (
    controlElement: HTMLElement,
    labelElement?: HTMLElement,
    errorElement?: HTMLElement
  ) => {
    const controlId = controlElement.id || ariaHelpers.generateId('control');
    controlElement.id = controlId;

    if (labelElement) {
      labelElement.setAttribute('for', controlId);
    }

    if (errorElement) {
      const errorId = errorElement.id || ariaHelpers.generateId('error');
      errorElement.id = errorId;
      controlElement.setAttribute('aria-describedby', errorId);
      controlElement.setAttribute('aria-invalid', 'true');
    }
  },

  /**
   * Create accessible form validation
   */
  createFormValidation: (
    formElement: HTMLFormElement,
    onValidationChange: (isValid: boolean, errors: string[]) => void
  ) => {
    const validateForm = () => {
      const errors: string[] = [];
      const formData = new FormData(formElement);

      // Basic validation - extend as needed
      formData.forEach((value, key) => {
        const element = formElement.elements.namedItem(key) as HTMLInputElement;
        if (element?.required && !value) {
          errors.push(`${element.labels?.[0]?.textContent || key} is required`);
        }
      });

      const isValid = errors.length === 0;
      onValidationChange(isValid, errors);

      if (!isValid) {
        announceToScreenReader(`Form has ${errors.length} errors`, 'assertive');
      }

      return isValid;
    };

    formElement.addEventListener('submit', (event) => {
      if (!validateForm()) {
        event.preventDefault();
      }
    });

    return validateForm;
  },
};

// Export all helpers as a single object
export const a11y = {
  focus: focusManagement,
  announce: announceToScreenReader,
  keyboard: keyboardNavigation,
  aria: ariaHelpers,
  visual: visualHelpers,
  touch: touchHelpers,
  form: formHelpers,
};

export default a11y;
/**
 * Accessibility utilities for TradeSense
 */

// ARIA label generators
export const generateAriaLabel = {
  tradeCard: (trade: any) => 
    `Trade ${trade.symbol}, entry ${trade.entry_price}, ${trade.pnl > 0 ? 'profit' : 'loss'} ${Math.abs(trade.pnl)}`,

  metric: (label: string, value: string | number) => 
    `${label}: ${value}`,

  button: (action: string, context?: string) => 
    context ? `${action} ${context}` : action,

  chart: (type: string, description: string) => 
    `${type} chart showing ${description}`,
};

// Accessibility utilities for TradeSense

// Focus management
export const trapFocus = (element: HTMLElement) => {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    }
  });
};

// Announce to screen readers
export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.setAttribute('class', 'sr-only');
  announcement.textContent = message;

  document.body.appendChild(announcement);

  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

// Keyboard navigation helpers
export const handleEscapeKey = (callback: () => void) => {
  return (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      callback();
    }
  };
};

export const handleEnterKey = (callback: () => void) => {
  return (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      callback();
    }
  };
};

// Color contrast checker
export const checkColorContrast = (foreground: string, background: string): boolean => {
  // Simplified contrast check (should use a proper library in production)
  const getLuminance = (color: string): number => {
    // This is a simplified version - in production use a proper color library
    const rgb = color.match(/\d+/g);
    if (!rgb) return 0;

    const [r, g, b] = rgb.map(Number);
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  };

  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  const contrast = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

  return contrast >= 4.5; // WCAG AA standard
};

// Accessibility audit helper
export const auditAccessibility = () => {
  const issues: string[] = [];

  // Check for missing alt text
  const images = document.querySelectorAll('img:not([alt])');
  if (images.length > 0) {
    issues.push(`${images.length} images missing alt text`);
  }

  // Check for missing form labels
  const inputs = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
  const unlabeledInputs = Array.from(inputs).filter(input => {
    const id = input.getAttribute('id');
    return !id || !document.querySelector(`label[for="${id}"]`);
  });

  if (unlabeledInputs.length > 0) {
    issues.push(`${unlabeledInputs.length} form inputs missing labels`);
  }

  // Check for insufficient color contrast (simplified)
  const buttons = document.querySelectorAll('button');
  buttons.forEach((button, index) => {
    const style = getComputedStyle(button);
    const color = style.color;
    const backgroundColor = style.backgroundColor;

    if (color && backgroundColor && !checkColorContrast(color, backgroundColor)) {
      issues.push(`Button ${index + 1} may have insufficient color contrast`);
    }
  });

  return issues;
};

// Skip links helper
export const addSkipLinks = () => {
  const skipLink = document.createElement('a');
  skipLink.href = '#main-content';
  skipLink.textContent = 'Skip to main content';
  skipLink.className = 'skip-link sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded';

  document.body.insertBefore(skipLink, document.body.firstChild);
};

// Keyboard navigation helpers
export const keyboardNavigation = {
  handleArrowKeys: (
    e: KeyboardEvent, 
    items: HTMLElement[], 
    currentIndex: number,
    onIndexChange: (newIndex: number) => void
  ) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        const nextIndex = Math.min(currentIndex + 1, items.length - 1);
        onIndexChange(nextIndex);
        items[nextIndex]?.focus();
        break;
      case 'ArrowUp':
        e.preventDefault();
        const prevIndex = Math.max(currentIndex - 1, 0);
        onIndexChange(prevIndex);
        items[prevIndex]?.focus();
        break;
      case 'Home':
        e.preventDefault();
        onIndexChange(0);
        items[0]?.focus();
        break;
      case 'End':
        e.preventDefault();
        const lastIndex = items.length - 1;
        onIndexChange(lastIndex);
        items[lastIndex]?.focus();
        break;
    }
  },
};

// Color contrast checker
export const accessibility = {
  checkColorContrast: (foreground: string, background: string): boolean => {
    // Simplified contrast ratio calculation
    // In a real implementation, you'd use a proper color contrast library
    const getLuminance = (color: string): number => {
      // Convert hex to RGB and calculate relative luminance
      const hex = color.replace('#', '');
      const r = parseInt(hex.substr(0, 2), 16) / 255;
      const g = parseInt(hex.substr(2, 2), 16) / 255;
      const b = parseInt(hex.substr(4, 2), 16) / 255;

      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };

    const l1 = getLuminance(foreground);
    const l2 = getLuminance(background);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

    return ratio >= 4.5; // WCAG AA standard
  },

  addSkipLink: () => {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = 'Skip to main content';
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      text-decoration: none;
      border-radius: 4px;
      z-index: 1000;
    `;

    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px';
    });

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';
    });

    document.body.insertBefore(skipLink, document.body.firstChild);
  },
};

// Screen reader utilities
export const screenReader = {
  hideFromScreenReader: (element: HTMLElement) => {
    element.setAttribute('aria-hidden', 'true');
  },

  showToScreenReader: (element: HTMLElement) => {
    element.removeAttribute('aria-hidden');
  },

  setLiveRegion: (element: HTMLElement, politeness: 'polite' | 'assertive' = 'polite') => {
    element.setAttribute('aria-live', politeness);
    element.setAttribute('aria-atomic', 'true');
  },
};