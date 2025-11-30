# AudiophileNAS
Linux-based Hi-Res Audio playback system

## Goal
Bit-perfect audio player with automatic file repair and NAS support

## Technologies
- MPD + ALSA
- Python/Flask
- FFmpeg, SoX
- Raspberry Pi

## Supported Formats
- Lossless: FLAC, WAV, ALAC, APE, **DSD (DSF/DFF)**
- Lossy: MP3, AAC, M4A, OGG, Opus
- Hi-Res: Up to DSD256, 384kHz/32-bit

## Structure
- backend/ - Flask API
- frontend/ - Web UI
- features/audio-repair/ - Audio file repair
- nas-integration/ - NAS connectivity

## Developer
Dan Shani - 2025

