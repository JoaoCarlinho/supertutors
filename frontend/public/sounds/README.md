# Celebration Sound Effects

This directory contains audio files for the celebration system.

## Required Sound Files

The following MP3 files should be placed in this directory:

- **celebration-1.mp3** - Light celebration sound (3-in-a-row)
- **celebration-2.mp3** - Medium celebration sound (6-in-a-row)
- **celebration-3.mp3** - Strong celebration sound (9-in-a-row)
- **streak-milestone.mp3** - Epic milestone sound (15+ streak)

## Sound Guidelines

- Format: MP3
- Duration: 1-3 seconds
- Volume: Normalized to consistent levels
- Style: Positive, encouraging, upbeat

## Placeholder Behavior

Currently, the audioService will gracefully handle missing files by logging warnings to the console. The celebration animations and UI will still work even if sound files are not present.

## Recommended Sources

- Free sound libraries: Freesound.org, Zapsplat.com
- Create custom sounds using: GarageBand, Audacity
- AI-generated: ElevenLabs Sound Effects
