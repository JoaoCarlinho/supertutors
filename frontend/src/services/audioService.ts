/**
 * Audio Service - Manages celebration sound playback
 * Implements PRD FR-5.2: Audio feedback with 7+ variations
 */

class AudioService {
  private audioCache: Map<string, HTMLAudioElement> = new Map();
  private isMuted: boolean = false;
  private volume: number = 0.5;
  private autoplayBlocked: boolean = false;

  constructor() {
    // Load settings from localStorage (AC-5)
    this.loadSettings();
  }

  /**
   * Load settings from localStorage
   */
  private loadSettings() {
    const savedVolume = localStorage.getItem('audioVolume');
    const savedMuted = localStorage.getItem('audioMuted');

    if (savedVolume) {
      this.volume = parseFloat(savedVolume);
    }
    if (savedMuted) {
      this.isMuted = savedMuted === 'true';
    }
  }

  /**
   * Save settings to localStorage
   */
  private saveSettings() {
    localStorage.setItem('audioVolume', this.volume.toString());
    localStorage.setItem('audioMuted', this.isMuted.toString());
  }

  /**
   * Preload audio files (AC-4: <100ms playback latency)
   * PRD FR-5.2: 7+ audio cheer variations
   */
  preloadSounds() {
    const sounds = [
      // Correct answer cheers (5 variations for randomization)
      '/sounds/correct-1.mp3',
      '/sounds/correct-2.mp3',
      '/sounds/correct-3.mp3',
      '/sounds/correct-4.mp3',
      '/sounds/correct-5.mp3',
      // Streak milestone celebrations
      '/sounds/celebration-1.mp3', // 3-in-a-row
      '/sounds/celebration-2.mp3', // 6-in-a-row
      '/sounds/celebration-3.mp3', // 9-in-a-row
      '/sounds/streak-milestone.mp3', // 15+ streak
    ];

    sounds.forEach((soundPath) => {
      const audio = new Audio(soundPath);
      audio.volume = this.volume;
      audio.preload = 'auto';

      // Handle load errors gracefully (AC-6)
      audio.addEventListener('error', () => {
        console.warn(`Failed to load sound: ${soundPath}`);
      });

      this.audioCache.set(soundPath, audio);
    });
  }

  /**
   * Play celebration sound based on streak count (PRD FR-5.1)
   * For correct answers, plays randomized cheer (AC-2)
   * For streaks, plays milestone-based celebration
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
    } else if (streak >= 3) {
      soundPath = '/sounds/celebration-1.mp3';
    } else {
      // For every correct answer (streak < 3), randomize sound (AC-2)
      const randomIndex = Math.floor(Math.random() * 5) + 1;
      soundPath = `/sounds/correct-${randomIndex}.mp3`;
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

      // Clone audio for concurrent playback
      const audioClone = audio.cloneNode(true) as HTMLAudioElement;
      audioClone.volume = this.volume;

      // Play with autoplay policy handling (AC-6)
      audioClone.play().catch((error) => {
        if (error.name === 'NotAllowedError') {
          this.autoplayBlocked = true;
          console.warn('Audio autoplay blocked by browser. User interaction required.');
        } else {
          console.warn(`Failed to play sound: ${soundPath}`, error);
        }
      });
    } catch (error) {
      console.warn(`Error playing sound: ${soundPath}`, error);
    }
  }

  /**
   * Set volume (0.0 to 1.0) - AC-3
   */
  setVolume(volume: number) {
    this.volume = Math.max(0, Math.min(1, volume));
    this.saveSettings();

    // Update volume for all cached audio
    this.audioCache.forEach((audio) => {
      audio.volume = this.volume;
    });
  }

  /**
   * Mute/unmute audio - AC-5
   */
  setMuted(muted: boolean) {
    this.isMuted = muted;
    this.saveSettings();
  }

  /**
   * Toggle mute state - AC-5
   */
  toggleMute(): boolean {
    this.isMuted = !this.isMuted;
    this.saveSettings();
    return this.isMuted;
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

  /**
   * Check if autoplay is blocked - AC-6
   */
  isAutoplayBlocked(): boolean {
    return this.autoplayBlocked;
  }

  /**
   * Request audio permission from user - AC-6
   * Call after user interaction to unlock autoplay
   */
  async requestAudioPermission(): Promise<boolean> {
    try {
      // Try to play silent audio to unlock
      const audio = new Audio();
      audio.volume = 0;
      await audio.play();
      this.autoplayBlocked = false;
      return true;
    } catch (error) {
      console.warn('Could not unlock audio:', error);
      return false;
    }
  }
}

// Export singleton instance
export const audioService = new AudioService();

// Preload sounds on initialization
audioService.preloadSounds();
