"""
Core metadata processing models and interfaces.
"""

from .models import AudioMetadata, MetadataSearchResult, AudioFileInfo
from .exceptions import MetadataProcessingError, MusicBrainzError, FileProcessingError
from .interfaces import MetadataExtractorInterface, MetadataWriterInterface, MetadataParserInterface

__all__ = [
    'AudioMetadata',
    'MetadataSearchResult', 
    'AudioFileInfo',
    'MetadataProcessingError',
    'MusicBrainzError',
    'FileProcessingError',
    'MetadataExtractorInterface',
    'MetadataWriterInterface',
    'MetadataParserInterface'
]