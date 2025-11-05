/**
 * Celebration Logic - Kea state management for celebration system
 */
import { kea } from 'kea';
import { getSocket } from '../lib/socketService';

export interface CelebrationData {
  achievement_type: string;
  streak: number;
  timestamp: string;
}

export const celebrationLogic = kea({
  path: ['celebration'],
  actions: {
    // @ts-expect-error - Kea action typing requires kea-typegen
    setStreak: (streak: number) => ({ streak }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    triggerCelebration: (data: CelebrationData) => ({ data }),
    clearCelebration: () => ({}),
    // @ts-expect-error - Kea action typing requires kea-typegen
    addToHistory: (data: CelebrationData) => ({ data }),
    incrementStreak: () => ({}),
    resetStreak: () => ({}),
  },

  reducers: {
    currentStreak: [
      0,
      {
        setStreak: (_, { streak }) => streak,
        incrementStreak: (state) => state + 1,
        resetStreak: () => 0,
      },
    ],

    activeCelebration: [
      null as CelebrationData | null,
      {
        triggerCelebration: (_, { data }) => data,
        clearCelebration: () => null,
      },
    ],

    celebrationHistory: [
      [] as CelebrationData[],
      {
        addToHistory: (state, { data }) => [data, ...state].slice(0, 10), // Keep last 10
      },
    ],

    isCelebrating: [
      false,
      {
        triggerCelebration: () => true,
        clearCelebration: () => false,
      },
    ],
  },

  listeners: ({ actions }) => ({
    triggerCelebration: ({ data }) => {
      // Add to history
      actions.addToHistory(data);

      // Auto-clear celebration after 5 seconds
      setTimeout(() => {
        actions.clearCelebration();
      }, 5000);
    },
  }),

  events: ({ actions, cache }) => ({
    afterMount: () => {
      // Listen for celebration events from server
      const socket = getSocket();
      if (!socket) {
        console.warn('[CelebrationLogic] Socket not initialized');
        return;
      }

      cache.celebrationHandler = (data: CelebrationData) => {
        console.log('Celebration triggered:', data);
        actions.triggerCelebration(data);
        actions.setStreak(data.streak);
      };

      socket.on('celebration:trigger', cache.celebrationHandler);
    },

    beforeUnmount: () => {
      // Clean up socket listener
      const socket = getSocket();
      if (socket && cache.celebrationHandler) {
        socket.off('celebration:trigger', cache.celebrationHandler);
      }
    },
  }),
});
