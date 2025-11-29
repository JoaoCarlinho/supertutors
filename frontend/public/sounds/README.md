# Celebration Sound Effects

This directory contains audio files for the celebration system (PRD FR-5.2).

## Required Sound Files (9 total - exceeds PRD requirement of 7+ variations)

The following MP3 files should be placed in this directory:

### Correct Answer Cheers (5 variations - randomized for variety)
- **correct-1.mp3** - Short positive cheer (e.g., "ding", "chime")
- **correct-2.mp3** - Short positive cheer (e.g., "whoosh", "tada")
- **correct-3.mp3** - Short positive cheer (e.g., "bell", "success")
- **correct-4.mp3** - Short positive cheer (e.g., "coin", "win")
- **correct-5.mp3** - Short positive cheer (e.g., "achievement")

### Streak Milestone Celebrations (4 variations)
- **celebration-1.mp3** - Light celebration sound (3-in-a-row streak)
- **celebration-2.mp3** - Medium celebration sound (6-in-a-row streak)
- **celebration-3.mp3** - Strong celebration sound (9-in-a-row streak)
- **streak-milestone.mp3** - Epic milestone sound (15+ streak)

## Sound Guidelines

- **Format:** MP3 (max 100KB per file for fast loading)
- **Duration:** 1-2 seconds each
- **Volume:** Normalized to consistent levels
- **Style:** Positive, encouraging, upbeat

## How to Download Free Sounds

### Option 1: Mixkit (Recommended - Free, No Attribution Required)
1. Visit: https://mixkit.co/free-sound-effects/win/
2. Download these sounds:
   - "Achievement bell" → rename to `correct-1.mp3`
   - "Quick win video game notification" → rename to `correct-2.mp3`
   - "Winning notification" → rename to `correct-3.mp3`
   - "Instant win" → rename to `correct-4.mp3`
   - "Small win" → rename to `correct-5.mp3`
3. Visit: https://mixkit.co/free-sound-effects/game/
   - "Retro game notification" → rename to `celebration-1.mp3`
   - "Winning chimes" → rename to `celebration-2.mp3`
   - "Winning swoosh" → rename to `celebration-3.mp3`
4. For milestone sound, visit: https://mixkit.co/free-sound-effects/game/
   - "Arcade bonus alert" → rename to `streak-milestone.mp3`

### Option 2: Freesound.org (CC0 Licensed)
1. Visit: https://freesound.org/
2. Search for: "game win achievement notification"
3. Filter by: License → CC0 (Public Domain)
4. Download 9 short (1-2s) positive sounds
5. Rename according to the list above

### Option 3: Zapsplat.com (Free with Attribution)
1. Visit: https://www.zapsplat.com/sound-effect-category/game-sounds/
2. Filter by CC0 license
3. Download celebration and achievement sounds

## Quick Installation

```bash
# After downloading, move files to this directory:
cd frontend/public/sounds
# Place your 9 MP3 files here

# Verify all files are present:
ls -la
```

## Placeholder Behavior

The audioService will gracefully handle missing files by logging warnings to the console. The celebration animations and UI will still work even if sound files are not present.

## Testing

After adding sound files, the audio system will:
- Play randomized cheers on every correct answer (AC-2)
- Play escalating celebrations at 3, 6, 9, and 15+ streaks (AC-1)
- Support volume control (0-100%, default 50%) (AC-3)
- Support mute toggle (persisted in localStorage) (AC-5)
- Preload all sounds for <100ms playback latency (AC-4)

## License Compliance

Ensure all downloaded sounds are:
- Royalty-free or CC0 licensed
- Appropriate for educational use
- No attribution required (or attribution added if required)
