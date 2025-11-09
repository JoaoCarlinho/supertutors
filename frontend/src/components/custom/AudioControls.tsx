/**
 * Audio Controls Component
 * Implements PRD FR-5.2 AC-5: Mute toggle and volume control
 * WCAG 2.1 AA accessible audio controls
 */
import { useState, useEffect } from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { audioService } from '../../services/audioService';

export function AudioControls() {
  const [isMuted, setIsMuted] = useState(audioService.getMuted());
  const [volume, setVolume] = useState(audioService.getVolume());
  const [showVolumeSlider, setShowVolumeSlider] = useState(false);

  useEffect(() => {
    // Initialize audio service
    audioService.preloadSounds();
  }, []);

  const handleMuteToggle = () => {
    const newMutedState = audioService.toggleMute();
    setIsMuted(newMutedState);
  };

  const handleVolumeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(event.target.value);
    setVolume(newVolume);
    audioService.setVolume(newVolume);
  };

  return (
    <div className="relative flex items-center gap-2">
      {/* Mute Toggle Button - AC-5 */}
      <button
        onClick={handleMuteToggle}
        onMouseEnter={() => setShowVolumeSlider(true)}
        onMouseLeave={() => setShowVolumeSlider(false)}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label={isMuted ? 'Unmute audio' : 'Mute audio'}
        title={isMuted ? 'Unmute audio' : 'Mute audio'}
      >
        {isMuted ? (
          <VolumeX className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        ) : (
          <Volume2 className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        )}
      </button>

      {/* Volume Slider - AC-3 */}
      {showVolumeSlider && !isMuted && (
        <div
          className="absolute left-full ml-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 z-50"
          onMouseEnter={() => setShowVolumeSlider(true)}
          onMouseLeave={() => setShowVolumeSlider(false)}
        >
          <div className="flex items-center gap-3">
            <label htmlFor="volume-slider" className="sr-only">
              Volume control
            </label>
            <input
              id="volume-slider"
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={volume}
              onChange={handleVolumeChange}
              className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
              aria-label="Volume"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(volume * 100)}
            />
            <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[3ch]">
              {Math.round(volume * 100)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
