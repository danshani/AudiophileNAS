"""
Metadata parser implementing the MetadataExtractorInterface.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

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

# שים לב לנתיב היחסי - אם זה נכשל, נסה לשנות ל-absolute
from ..core.interfaces import MetadataExtractorInterface
from ..core.models import AudioMetadata, AudioFileInfo
from ..core.exceptions import FileProcessingError

logger = logging.getLogger(__name__)

class MetadataParser(MetadataExtractorInterface):
    """Extract metadata from audio files using Mutagen."""
    
    def __init__(self):
        if not MUTAGEN_AVAILABLE:
            raise ImportError("Mutagen library is required for metadata extraction")
        
        self.format_mappings = {
            'flac': { 'title': 'TITLE', 'artist': 'ARTIST', 'album': 'ALBUM', 'date': 'DATE', 'genre': 'GENRE', 'track_number': 'TRACKNUMBER', 'album_artist': 'ALBUMARTIST', 'composer': 'COMPOSER' },
            'mp3': { 'title': 'TIT2', 'artist': 'TPE1', 'album': 'TALB', 'date': 'TDRC', 'genre': 'TCON', 'track_number': 'TRCK', 'album_artist': 'TPE2', 'composer': 'TCOM' },
            'mp4': { 'title': '\xa9nam', 'artist': '\xa9ART', 'album': '\xa9alb', 'date': '\xa9day', 'genre': '\xa9gen', 'track_number': 'trkn', 'album_artist': 'aART', 'composer': '\xa9wrt' }
        }
        self.supported_formats = {'flac', 'mp3', 'mp4', 'ogg', 'wav'}
    
    def extract_metadata(self, file_path: Path) -> AudioMetadata:
        if not file_path.exists():
            raise FileProcessingError(f"File not found: {file_path}", str(file_path), "extract")
        
        try:
            audio_file = mutagen.File(str(file_path))
            if audio_file is None:
                return AudioMetadata(source="embedded")
            
            file_format = self._detect_format(audio_file)
            metadata = self._extract_by_format(audio_file, file_format)
            metadata.file_info = self.extract_file_info(file_path)
            metadata.source = "embedded"
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise FileProcessingError(f"Metadata extraction failed: {e}", str(file_path), "extract")
    
    def extract_file_info(self, file_path: Path) -> AudioFileInfo:
        try:
            audio_file = mutagen.File(str(file_path))
            file_format = self._detect_format(audio_file) if audio_file else 'unknown'
            file_info = AudioFileInfo(
                file_path=file_path, file_format=file_format, file_size=file_path.stat().st_size,
                duration=0.0, bitrate=0, sample_rate=0, channels=0, bits_per_sample=0
            )
            if audio_file and hasattr(audio_file, 'info'):
                info = audio_file.info
                file_info.duration = getattr(info, 'length', 0.0)
                file_info.bitrate = getattr(info, 'bitrate', 0)
                file_info.sample_rate = getattr(info, 'sample_rate', 0)
                file_info.channels = getattr(info, 'channels', 0)
                file_info.bits_per_sample = getattr(info, 'bits_per_sample', 0)
            return file_info
        except Exception as e:
            logger.error(f"Error extracting file info from {file_path}: {e}")
            raise FileProcessingError(f"File info extraction failed: {e}", str(file_path), "extract_info")
    
    def supports_format(self, file_format: str) -> bool:
        return file_format.lower() in self.supported_formats
    
    def _detect_format(self, audio_file) -> str:
        if audio_file is None: return 'unknown'
        mapping = {'FLAC': 'flac', 'MP3': 'mp3', 'MP4': 'mp4', 'OggVorbis': 'ogg', 'WAVE': 'wav'}
        return mapping.get(type(audio_file).__name__, 'unknown')
    
    def _extract_by_format(self, audio_file, file_format: str) -> AudioMetadata:
        metadata = AudioMetadata()
        if file_format not in self.format_mappings: return self._extract_generic(audio_file)
        for standard_key, format_key in self.format_mappings[file_format].items():
            value = self._get_tag_value(audio_file, format_key)
            if value: setattr(metadata, standard_key, value)
        return metadata
    
    def _extract_generic(self, audio_file) -> AudioMetadata:
        metadata = AudioMetadata()
        common_mappings = {
            'title': ['TITLE', 'TIT2', '\xa9nam'], 'artist': ['ARTIST', 'TPE1', '\xa9ART'],
            'album': ['ALBUM', 'TALB', '\xa9alb'], 'date': ['DATE', 'TDRC', '\xa9day'],
            'genre': ['GENRE', 'TCON', '\xa9gen'], 'track_number': ['TRACKNUMBER', 'TRCK', 'trkn']
        }
        for standard_key, possible_keys in common_mappings.items():
            for key in possible_keys:
                value = self._get_tag_value(audio_file, key)
                if value:
                    setattr(metadata, standard_key, value)
                    break
        return metadata
    
    def _get_tag_value(self, audio_file, key: str) -> Optional[str]:
        try:
            if key in audio_file:
                value = audio_file[key]
                if isinstance(value, list) and len(value) > 0: return str(value[0])
                elif isinstance(value, (str, int, float)): return str(value)
        except (KeyError, AttributeError): pass
        return None

# --- ALIAS FOR COMPATIBILITY ---
MetadataExtractor = MetadataParser