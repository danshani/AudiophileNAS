"""
Professional metadata processing module for AudiophileNAS.

This module provides a clean, extensible architecture for audio metadata processing
using MusicBrainz API integration with proper separation of concerns.

Architecture:
- Core: Data models, interfaces, and exceptions
- Services: Business logic and orchestration  
- Parsers: Metadata extraction from files and filenames
- Writers: Metadata writing to audio files
- Config: Configuration management
- CLI: Command-line interface
"""

# Core models and interfaces
from .core.models import AudioMetadata, AudioFileInfo, MetadataSearchResult, ProcessingResult
from .core.exceptions import MetadataProcessingError, MusicBrainzError, FileProcessingError

# Main service interface
from .services.metadata_service import MetadataService
from .services.file_service import FileService
from .services.musicbrainz_service import MusicBrainzService

# Configuration
from .config import MUSICBRAINZ_CONFIG, METADATA_CONFIG

# Legacy compatibility (deprecated)
from .metadata_completer import MetadataCompleter
from .metadata_extractor import MetadataExtractor  
from .metadata_writer import MetadataWriter

__version__ = "2.0.0"

__all__ = [
    # Core models
    'AudioMetadata',
    'AudioFileInfo', 
    'MetadataSearchResult',
    'ProcessingResult',
    
    # Exceptions
    'MetadataProcessingError',
    'MusicBrainzError', 
    'FileProcessingError',
    
    # Main services
    'MetadataService',
    'FileService',
    'MusicBrainzService',
    
    # Configuration
    'MUSICBRAINZ_CONFIG',
    'METADATA_CONFIG',
    
    # Legacy (deprecated)
    'MetadataCompleter',
    'MetadataExtractor',
    'MetadataWriter',
]