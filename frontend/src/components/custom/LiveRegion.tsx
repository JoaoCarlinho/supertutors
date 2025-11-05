import React from 'react';

/**
 * ARIA Live Regions - For screen reader announcements
 */
export const LiveRegion: React.FC = () => {
  return (
    <>
      {/* Polite announcements (don't interrupt) */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        id="polite-announcer"
      />

      {/* Assertive announcements (urgent, interrupt) */}
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
        id="assertive-announcer"
      />
    </>
  );
};
