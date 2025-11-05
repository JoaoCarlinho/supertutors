/**
 * Accessibility Utilities - Screen reader announcements and focus management
 */

/**
 * Announce message to screen readers
 */
export const announce = (
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
): void => {
  const liveRegion = document.querySelector(`[aria-live="${priority}"]`);
  if (liveRegion) {
    liveRegion.textContent = message;
    // Clear after announcement
    setTimeout(() => {
      liveRegion.textContent = '';
    }, 1000);
  }
};

/**
 * Focus element by selector
 */
export const focusElement = (selector: string): void => {
  const element = document.querySelector(selector) as HTMLElement;
  if (element) {
    element.focus();
  }
};

/**
 * Focus first focusable element in container
 */
export const focusFirstElement = (containerSelector: string): void => {
  const container = document.querySelector(containerSelector);
  const firstFocusable = container?.querySelector(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  ) as HTMLElement;
  if (firstFocusable) {
    firstFocusable.focus();
  }
};

/**
 * Get all focusable elements in container
 */
export const getFocusableElements = (container: HTMLElement): HTMLElement[] => {
  const focusableSelectors = [
    'button:not([disabled])',
    '[href]',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ];

  const elements = container.querySelectorAll(focusableSelectors.join(', '));
  return Array.from(elements) as HTMLElement[];
};

/**
 * Trap focus within container (for modals)
 */
export const trapFocus = (
  container: HTMLElement,
  event: KeyboardEvent
): void => {
  const focusableElements = getFocusableElements(container);
  if (focusableElements.length === 0) return;

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  if (event.key !== 'Tab') return;

  if (event.shiftKey) {
    // Shift + Tab
    if (document.activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    }
  } else {
    // Tab
    if (document.activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }
};

/**
 * Check if device is mobile
 */
export const isMobileDevice = (): boolean => {
  return window.innerWidth < 768;
};

/**
 * Get contrast ratio between two colors
 */
export const getContrastRatio = (color1: string, color2: string): number => {
  // Simplified contrast calculation - placeholder implementation
  // In production, use a proper color library to calculate actual luminance
  const l1 = 0.5; // getLuminance(color1)
  const l2 = 0.5; // getLuminance(color2)
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  // Suppress unused variable warnings - color1 and color2 will be used
  // when proper luminance calculation is implemented
  void color1;
  void color2;

  return (lighter + 0.05) / (darker + 0.05);
};
