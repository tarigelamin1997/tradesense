
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
 * Provides helpers for keyboard navigation, screen readers, and ARIA attributes
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
