# AudiophileNAS

A comprehensive audio file management system with advanced metadata processing capabilities.

## Features

### 🎵 Metadata Processing
- **Smart Metadata Completion** - Automatically complete missing metadata using MusicBrainz
- **Filename Parsing** - Extract metadata from structured filenames  
- **Character Encoding Fix** - Handle corrupted UTF-8 characters
- **Genre Detection** - Intelligent genre detection from multiple sources
- **Batch Processing** - Process entire music collections efficiently
- **Safe Operations** - Automatic backups before any file modifications

### 🏗️ Architecture
- **Clean Architecture** - Service layer pattern with proper separation of concerns
- **Strong Typing** - Type-safe data models and interfaces
- **Extensible Design** - Plugin-based architecture for easy extension
- **Comprehensive Error Handling** - Graceful degradation and detailed logging

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Basic Usage
```python
from features.audio_repair.metadata import MetadataService

# Initialize service
service = MetadataService()

# Process a single file
from pathlib import Path
result = service.process_file(Path("path/to/audio/file.flac"))

if result.success:
    print(f"✅ {result.metadata.title} - {result.metadata.artist}")
    print(f"Genre: {result.metadata.genre}")
else:
    print(f"❌ Error: {result.error}")
```

### Command Line Interface
```bash
# Process a directory with metadata completion
cd features/audio-repair/metadata
python -m cli.commands ../test_audio --write --verbose

# Dry run (see what would be changed)
python -m cli.commands ../test_audio --dry-run --verbose
```

## Documentation

- [Usage Examples](docs/examples/metadata_usage_examples.py)
- [Metadata System README](features/audio-repair/metadata/README.md)

## System Capabilities

### Real-World Results
From actual testing on audio collections:

- **83% Success Rate** - On challenging test collection with mixed formats
- **Character Encoding Fixes** - Successfully handles corrupted Finnish characters  
- **Genre Detection** - Finds genre information from MusicBrainz releases
- **Filename Parsing** - Extracts metadata from structured filenames
- **Perfect Matches** - Achieves 100% confidence scores for exact matches

### Supported Formats
- **FLAC** - Full support (recommended)
- **MP3** - Full support with ID3v2 tags
- **MP4/M4A** - Full support with iTunes tags
- **OGG** - Basic support
- **WAV** - Limited metadata support

## Architecture

```
AudiophileNAS/
├── features/
│   └── audio-repair/
│       ├── metadata/          # Complete metadata processing system
│       │   ├── core/          # Data models and interfaces
│       │   ├── services/      # Business logic
│       │   ├── parsers/       # Metadata extraction
│       │   ├── writers/       # Metadata writing
│       │   └── cli/           # Command-line interface
│       └── test_audio/        # Test audio files
├── docs/
│   └── examples/              # Usage examples
└── config files...
```

## Development

### Running the System
```bash
# Test with sample files
cd features/audio-repair/metadata
python -m cli.commands ../test_audio --verbose

# Use as Python module
python -c "from features.audio_repair.metadata import MetadataService; print('✅ System ready')"
```

## Developer
Dan Shani - 2025

