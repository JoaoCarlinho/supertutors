import React from 'react';

/**
 * Skip Navigation Links - Allows keyboard users to skip to main content
 */
export const SkipNav: React.FC = () => {
  return (
    <nav className="skip-nav">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <a href="#thread-list" className="skip-link">
        Skip to thread list
      </a>
      <a href="#chat-input" className="skip-link">
        Skip to chat input
      </a>
    </nav>
  );
};
