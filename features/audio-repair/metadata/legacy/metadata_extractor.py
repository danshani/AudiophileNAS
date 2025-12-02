"""
Metadata extractor for various audio file formats.
"""

import os
from typing import Dict, Optional, Any, List
import logging

try:
    import mutagen
    from mutagen.flac import FLAC
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    from mutagen.wave import WAVE
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from .config import FORMAT_METADATA_MAPPING

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Extracts metadata from audio files."""
    
    def __init__(self):
        if not MUTAGEN_AVAILABLE:
            raise ImportError("Mutagen library is required for metadata extraction")
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing extracted metadata
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {}
        
        try:
            audio_file = mutagen.File(file_path)
            if audio_file is None:
                logger.warning(f"Could not read metadata from: {file_path}")
                return {}
            
            file_format = self._detect_format(audio_file)
            metadata = self._extract_by_format(audio_file, file_format)
            
            # Add file information
            metadata['file_path'] = file_path
            metadata['file_format'] = file_format
            metadata['file_size'] = os.path.getsize(file_path)
            
            # Add audio properties if available
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                metadata['duration'] = getattr(info, 'length', 0)
                metadata['bitrate'] = getattr(info, 'bitrate', 0)
                metadata['sample_rate'] = getattr(info, 'sample_rate', 0)
                metadata['channels'] = getattr(info, 'channels', 0)
                metadata['bits_per_sample'] = getattr(info, 'bits_per_sample', 0)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return {}
    
    def _detect_format(self, audio_file) -> str:
        """Detect the audio file format."""
        format_mapping = {
            'FLAC': 'flac',
            'MP3': 'mp3', 
            'MP4': 'mp4',
            'OggVorbis': 'ogg',
            'WAVE': 'wav'
        }
        
        file_type = type(audio_file).__name__
        return format_mapping.get(file_type, 'unknown')
    
    def _extract_by_format(self, audio_file, file_format: str) -> Dict[str, Any]:
        """Extract metadata based on file format."""
        metadata = {}
        
        if file_format not in FORMAT_METADATA_MAPPING:
            return self._extract_generic(audio_file)
        
        mapping = FORMAT_METADATA_MAPPING[file_format]
        
        for standard_key, format_key in mapping.items():
            value = self._get_tag_value(audio_file, format_key)
            if value:
                metadata[standard_key] = value
        
        return metadata
    
    def _extract_generic(self, audio_file) -> Dict[str, Any]:
        """Generic metadata extraction when format mapping is not available."""
        metadata = {}
        
        # Common tag mappings to try
        common_mappings = {
            'title': ['TITLE', 'TIT2', '\xa9nam'],
            'artist': ['ARTIST', 'TPE1', '\xa9ART'],
            'album': ['ALBUM', 'TALB', '\xa9alb'],
            'date': ['DATE', 'TDRC', '\xa9day'],
            'genre': ['GENRE', 'TCON', '\xa9gen'],
            'track_number': ['TRACKNUMBER', 'TRCK', 'trkn']
        }
        
        for standard_key, possible_keys in common_mappings.items():
            for key in possible_keys:
                value = self._get_tag_value(audio_file, key)
                if value:
                    metadata[standard_key] = value
                    break
        
        return metadata
    
    def _get_tag_value(self, audio_file, key: str) -> Optional[str]:
        """Get tag value from audio file, handling different formats."""
        try:
            if key in audio_file:
                value = audio_file[key]
                
                # Handle list values
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                elif isinstance(value, (str, int, float)):
                    return str(value)
        except (KeyError, AttributeError):
            pass
        
        return None
    
    def get_missing_metadata_fields(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Identify which metadata fields are missing.
        
        Args:
            metadata: Current metadata dictionary
            
        Returns:
            List of missing field names
        """
        from .config import METADATA_CONFIG
        
        required_fields = METADATA_CONFIG['required_fields']
        missing = []
        
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                missing.append(field)
        
        return missing
    
    def is_metadata_complete(self, metadata: Dict[str, Any]) -> bool:
        """
        Check if metadata contains all required fields.
        
        Args:
            metadata: Metadata dictionary to check
            
        Returns:
            True if all required fields are present
        """
        return len(self.get_missing_metadata_fields(metadata)) == 0