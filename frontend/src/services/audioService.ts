/**
 * Audio Service - Manages celebration sound playback
 */

class AudioService {
  private audioCache: Map<string, HTMLAudioElement> = new Map();
  private isMuted: boolean = false;
  private volume: number = 0.5;

  /**
   * Preload audio files
   */
  preloadSounds() {
    const sounds = [
      '/sounds/celebration-1.mp3',
      '/sounds/celebration-2.mp3',
      '/sounds/celebration-3.mp3',
      '/sounds/streak-milestone.mp3',
    ];

    sounds.forEach((soundPath) => {
      const audio = new Audio(soundPath);
      audio.volume = this.volume;
      audio.preload = 'auto';

      // Handle load errors gracefully
      audio.addEventListener('error', () => {
        console.warn(`Failed to load sound: ${soundPath}`);
      });

      this.audioCache.set(soundPath, audio);
    });
  }

  /**
   * Play celebration sound based on streak count
   */
  playCelebration(streak: number) {
    if (this.isMuted) return;

    let soundPath: string;

    // Select sound based on streak milestone
    if (streak >= 15) {
      soundPath = '/sounds/streak-milestone.mp3';
    } else if (streak >= 9) {
      soundPath = '/sounds/celebration-3.mp3';
    } else if (streak >= 6) {
      soundPath = '/sounds/celebration-2.mp3';
    } else {
      soundPath = '/sounds/celebration-1.mp3';
    }

    this.playSound(soundPath);
  }

  /**
   * Play a specific sound
   */
  private playSound(soundPath: string) {
    try {
      let audio = this.audioCache.get(soundPath);

      if (!audio) {
        audio = new Audio(soundPath);
        audio.volume = this.volume;
        this.audioCache.set(soundPath, audio);
      }

      // Reset audio if already playing
      audio.currentTime = 0;
      audio.volume = this.volume;

      audio.play().catch((error) => {
        console.warn(`Failed to play sound: ${soundPath}`, error);
      });
    } catch (error) {
      console.warn(`Error playing sound: ${soundPath}`, error);
    }
  }

  /**
   * Set volume (0.0 to 1.0)
   */
  setVolume(volume: number) {
    this.volume = Math.max(0, Math.min(1, volume));

    // Update volume for all cached audio
    this.audioCache.forEach((audio) => {
      audio.volume = this.volume;
    });
  }

  /**
   * Mute/unmute audio
   */
  setMuted(muted: boolean) {
    this.isMuted = muted;
  }

  /**
   * Get current mute state
   */
  getMuted(): boolean {
    return this.isMuted;
  }

  /**
   * Get current volume
   */
  getVolume(): number {
    return this.volume;
  }
}

// Export singleton instance
export const audioService = new AudioService();

// Preload sounds on initialization
audioService.preloadSounds();
