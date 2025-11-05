/**
 * Keyboard Shortcuts Hook
 */
import { useEffect } from 'react';

export interface KeyboardShortcuts {
  onNewThread?: () => void;
  onToggleCanvas?: () => void;
  onCloseModal?: () => void;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcuts) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+N or Cmd+N: New thread
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        shortcuts.onNewThread?.();
      }

      // Ctrl+D or Cmd+D: Toggle canvas
      if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        shortcuts.onToggleCanvas?.();
      }

      // Escape: Close modal/overlay
      if (e.key === 'Escape') {
        shortcuts.onCloseModal?.();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
};
