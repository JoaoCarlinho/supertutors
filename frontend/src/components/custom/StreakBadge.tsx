import React from 'react';
import { useValues } from 'kea';
import { celebrationLogic } from '../../logic/celebrationLogic';

export const StreakBadge: React.FC = () => {
  const { currentStreak } = useValues(celebrationLogic);

  if (currentStreak === 0) {
    return null;
  }

  return (
    <div className="streak-badge fixed top-4 right-4 z-50 flex items-center gap-2 bg-gradient-to-r from-orange-500 to-pink-500 text-white px-4 py-2 rounded-full shadow-lg animate-pulse">
      <span className="text-2xl">🔥</span>
      <div className="flex flex-col">
        <span className="text-sm font-bold">{currentStreak} Streak</span>
        <span className="text-xs opacity-90">
          {currentStreak % 3 === 2
            ? '1 more for celebration!'
            : `${3 - (currentStreak % 3)} until next milestone`}
        </span>
      </div>
    </div>
  );
};
