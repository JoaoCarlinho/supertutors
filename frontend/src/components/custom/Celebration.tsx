import React, { useEffect, useState } from 'react';
import { useValues, useActions } from 'kea';
import { celebrationLogic } from '../../logic/celebrationLogic';
import { audioService } from '../../services/audioService';

export const Celebration: React.FC = () => {
  const { activeCelebration, isCelebrating } = useValues(celebrationLogic);
  const { clearCelebration } = useActions(celebrationLogic);
  const [confetti, setConfetti] = useState<Array<{ id: number; left: number; delay: number }>>([]);

  useEffect(() => {
    if (isCelebrating && activeCelebration) {
      // Play celebration sound
      audioService.playCelebration(activeCelebration.streak);

      // Generate confetti particles
      const particles = Array.from({ length: 30 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 0.5,
      }));
      setConfetti(particles);

      // Clear confetti after animation
      const timer = setTimeout(() => {
        setConfetti([]);
      }, 4000);

      return () => clearTimeout(timer);
    }
  }, [isCelebrating, activeCelebration]);

  if (!isCelebrating || !activeCelebration) {
    return null;
  }

  const { achievement_type, streak } = activeCelebration;

  return (
    <>
      {/* Confetti Effect */}
      <div className="celebration-confetti fixed inset-0 pointer-events-none z-50 overflow-hidden">
        {confetti.map((particle) => (
          <div
            key={particle.id}
            className="confetti-particle absolute -top-10 w-3 h-3 rounded-full animate-fall"
            style={{
              left: `${particle.left}%`,
              animationDelay: `${particle.delay}s`,
              backgroundColor: ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'][
                particle.id % 5
              ],
            }}
          />
        ))}
      </div>

      {/* Celebration Modal */}
      <div className="celebration-modal fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
        <div className="celebration-content bg-white rounded-2xl shadow-2xl p-8 max-w-md animate-bounce-in pointer-events-auto">
          <div className="text-center">
            {/* Animated Trophy/Star */}
            <div className="text-8xl mb-4 animate-spin-slow">
              {streak >= 15 ? '🏆' : streak >= 9 ? '⭐' : '🎉'}
            </div>

            {/* Achievement Text */}
            <h2 className="text-3xl font-bold text-gray-800 mb-2">
              {streak >= 15 ? 'Amazing!' : streak >= 9 ? 'Fantastic!' : 'Great Job!'}
            </h2>

            <p className="text-xl text-gray-600 mb-4">
              <span className="text-4xl font-bold text-orange-500">{streak}</span> correct answers
              in a row!
            </p>

            <div className="flex items-center justify-center gap-2 text-gray-500 mb-4">
              <span className="text-2xl">🔥</span>
              <span className="text-lg font-medium">{achievement_type}</span>
            </div>

            {/* Motivational Message */}
            <p className="text-sm text-gray-500 italic">
              {streak >= 15
                ? "You're on fire! Keep up this incredible momentum!"
                : streak >= 9
                ? "Outstanding progress! You're mastering these concepts!"
                : "Keep it up! You're doing great!"}
            </p>

            {/* Close Button */}
            <button
              onClick={clearCelebration}
              className="mt-6 px-6 py-2 bg-gradient-to-r from-orange-500 to-pink-500 text-white rounded-full font-medium hover:shadow-lg transition-shadow"
            >
              Continue Learning
            </button>
          </div>
        </div>
      </div>

      {/* Inline Styles for Animations */}
      <style>{`
        @keyframes fall {
          0% {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
          }
        }

        @keyframes bounce-in {
          0% {
            transform: scale(0.3);
            opacity: 0;
          }
          50% {
            transform: scale(1.05);
          }
          70% {
            transform: scale(0.9);
          }
          100% {
            transform: scale(1);
            opacity: 1;
          }
        }

        @keyframes spin-slow {
          0% {
            transform: rotate(0deg) scale(1);
          }
          50% {
            transform: rotate(180deg) scale(1.2);
          }
          100% {
            transform: rotate(360deg) scale(1);
          }
        }

        .confetti-particle {
          animation: fall 3s linear forwards;
        }

        .animate-bounce-in {
          animation: bounce-in 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }

        .animate-spin-slow {
          animation: spin-slow 2s ease-in-out infinite;
        }
      `}</style>
    </>
  );
};
