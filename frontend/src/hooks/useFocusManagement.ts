/**
 * Focus Management Hook
 */
import { useEffect, useRef } from 'react';
import { focusElement, focusFirstElement } from '../utils/accessibility';

export const useFocusManagement = () => {
  return {
    focusElement,
    focusFirstElement,
  };
};

/**
 * Focus Return Hook - Returns focus to trigger element when component unmounts
 */
export const useFocusReturn = (isOpen: boolean) => {
  const triggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Store currently focused element
      triggerRef.current = document.activeElement as HTMLElement;
    } else if (triggerRef.current) {
      // Return focus when closed
      triggerRef.current.focus();
      triggerRef.current = null;
    }
  }, [isOpen]);

  return triggerRef;
};

/**
 * Focus Trap Hook - Traps focus within container
 */
export const useFocusTrap = (
  containerRef: React.RefObject<HTMLElement>,
  isActive: boolean
) => {
  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const focusableElements = container.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown as EventListener);
    return () => container.removeEventListener('keydown', handleKeyDown as EventListener);
  }, [containerRef, isActive]);
};
