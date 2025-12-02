"""
Service layer for metadata processing.
"""

from .metadata_service import MetadataService
from .musicbrainz_service import MusicBrainzService  
from .file_service import FileService

__all__ = ['MetadataService', 'MusicBrainzService', 'FileService']