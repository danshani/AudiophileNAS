# Test Audio Files

This directory is for test audio files to validate the metadata processing system.

## Usage

Place small audio files here for testing:
- FLAC files (recommended for lossless testing)
- MP3 files (for lossy format testing)
- Other supported formats: MP4, OGG, WAV

## Size Guidelines

- Keep test files small (< 5MB each) to maintain repository lightweight
- Use short audio clips or samples
- Consider using silent/generated audio for basic metadata testing

## Testing

Run metadata processing on test files:

```bash
cd features/audio-repair/metadata
python -m cli.commands ../test_audio --verbose
```

## Note

Large test files (>50MB) have been removed to keep the repository lightweight.
Add your own test files as needed for development.