/**
 * Celebration Logic - Kea state management for celebration system
 * Implements PRD FR-5: Celebration & Motivation System
 */
import { kea } from 'kea';
import { getSocket } from '../lib/socketService';
import { audioService } from '../services/audioService';

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

      // Play audio feedback (PRD FR-5.2: Audio cheer on correct answer)
      audioService.playCelebration(data.streak);

      // Auto-clear celebration after 5 seconds
      setTimeout(() => {
        actions.clearCelebration();
      }, 5000);
    },
  }),

  events: ({ actions, cache }) => ({
    afterMount: () => {
      // Define the celebration handler
      cache.celebrationHandler = (data: CelebrationData) => {
        console.log('Celebration triggered:', data);
        actions.triggerCelebration(data);
        actions.setStreak(data.streak);
      };

      // Try to attach listener immediately
      const socket = getSocket();
      if (socket) {
        socket.on('celebration:trigger', cache.celebrationHandler);
        console.log('Celebration listener attached on mount');
      }

      // Also set up a polling mechanism to attach listener when socket becomes available
      cache.socketCheckInterval = setInterval(() => {
        const socket = getSocket();
        if (socket && !cache.listenerAttached) {
          socket.on('celebration:trigger', cache.celebrationHandler);
          cache.listenerAttached = true;
          clearInterval(cache.socketCheckInterval);
          console.log('Celebration listener attached after socket ready');
        }
      }, 100);

      // Clear interval after 10 seconds to prevent infinite checking
      setTimeout(() => {
        if (cache.socketCheckInterval) {
          clearInterval(cache.socketCheckInterval);
        }
      }, 10000);
    },

    beforeUnmount: () => {
      // Clean up socket listener
      const socket = getSocket();
      if (socket && cache.celebrationHandler) {
        socket.off('celebration:trigger', cache.celebrationHandler);
      }

      // Clear interval if still running
      if (cache.socketCheckInterval) {
        clearInterval(cache.socketCheckInterval);
      }
    },
  }),
});
