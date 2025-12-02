"""
Metadata writer for updating audio file metadata.
"""

import os
import logging
from typing import Dict, Any, Optional

try:
    import mutagen
    from mutagen.flac import FLAC
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from .config import FORMAT_METADATA_MAPPING

logger = logging.getLogger(__name__)

class MetadataWriter:
    """Write metadata back to audio files."""
    
    def __init__(self):
        if not MUTAGEN_AVAILABLE:
            raise ImportError("Mutagen library is required for metadata writing")
    
    def write_metadata(self, file_path: str, metadata: Dict[str, Any], 
                      backup: bool = True) -> bool:
        """
        Write metadata to an audio file.
        
        Args:
            file_path: Path to the audio file
            metadata: Metadata dictionary to write
            backup: Whether to create a backup before writing
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        try:
            # Create backup if requested
            if backup:
                self._create_backup(file_path)
            
            # Load the audio file
            audio_file = mutagen.File(file_path)
            if audio_file is None:
                logger.error(f"Could not load audio file: {file_path}")
                return False
            
            # Detect format and write metadata
            file_format = self._detect_format(audio_file)
            success = self._write_by_format(audio_file, file_format, metadata)
            
            if success:
                audio_file.save()
                logger.info(f"Metadata written successfully to: {file_path}")
                return True
            else:
                logger.error(f"Failed to write metadata to: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error writing metadata to {file_path}: {e}")
            return False
    
    def _create_backup(self, file_path: str):
        """Create a backup of the original file."""
        import shutil
        
        backup_path = f"{file_path}.backup"
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            logger.warning(f"Could not create backup for {file_path}: {e}")
    
    def _detect_format(self, audio_file) -> str:
        """Detect the audio file format."""
        format_mapping = {
            'FLAC': 'flac',
            'MP3': 'mp3',
            'MP4': 'mp4',
            'OggVorbis': 'ogg'
        }
        
        file_type = type(audio_file).__name__
        return format_mapping.get(file_type, 'unknown')
    
    def _write_by_format(self, audio_file, file_format: str, metadata: Dict[str, Any]) -> bool:
        """Write metadata based on file format."""
        if file_format not in FORMAT_METADATA_MAPPING:
            logger.warning(f"No format mapping available for: {file_format}")
            return False
        
        mapping = FORMAT_METADATA_MAPPING[file_format]
        
        try:
            for standard_key, format_key in mapping.items():
                if standard_key in metadata and metadata[standard_key]:
                    value = str(metadata[standard_key])
                    
                    # Handle special cases for different formats
                    if file_format == 'mp4' and format_key == 'trkn':
                        # MP4 track number format: (track, total)
                        track_num = self._parse_track_number(value)
                        if track_num:
                            audio_file[format_key] = [(track_num, 0)]
                    else:
                        audio_file[format_key] = [value]
            
            # Add MusicBrainz IDs if available
            self._write_musicbrainz_ids(audio_file, file_format, metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing metadata: {e}")
            return False
    
    def _parse_track_number(self, value: str) -> Optional[int]:
        """Parse track number from string."""
        try:
            # Handle formats like "3", "3/12", "03"
            if '/' in value:
                return int(value.split('/')[0])
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _write_musicbrainz_ids(self, audio_file, file_format: str, metadata: Dict[str, Any]):
        """Write MusicBrainz IDs to the file."""
        mb_mapping = {
            'flac': {
                'musicbrainz_recording_id': 'MUSICBRAINZ_TRACKID',
                'musicbrainz_release_id': 'MUSICBRAINZ_ALBUMID',
                'musicbrainz_artist_id': 'MUSICBRAINZ_ARTISTID'
            },
            'mp3': {
                'musicbrainz_recording_id': 'UFID:http://musicbrainz.org',
                'musicbrainz_release_id': 'TXXX:MusicBrainz Album Id',
                'musicbrainz_artist_id': 'TXXX:MusicBrainz Artist Id'
            },
            'mp4': {
                'musicbrainz_recording_id': '----:com.apple.iTunes:MusicBrainz Track Id',
                'musicbrainz_release_id': '----:com.apple.iTunes:MusicBrainz Album Id',
                'musicbrainz_artist_id': '----:com.apple.iTunes:MusicBrainz Artist Id'
            }
        }
        
        if file_format not in mb_mapping:
            return
        
        mapping = mb_mapping[file_format]
        
        for metadata_key, format_key in mapping.items():
            if metadata_key in metadata and metadata[metadata_key]:
                value = str(metadata[metadata_key])
                
                if file_format == 'mp3' and 'UFID' in format_key:
                    # Handle MP3 UFID frame specially
                    from mutagen.id3 import UFID
                    audio_file[format_key] = UFID(owner='http://musicbrainz.org', data=value.encode())
                elif file_format == 'mp3' and 'TXXX' in format_key:
                    # Handle MP3 TXXX frame
                    from mutagen.id3 import TXXX
                    desc = format_key.split(':')[1]
                    audio_file[format_key] = TXXX(encoding=3, desc=desc, text=value)
                elif file_format == 'mp4':
                    # Handle MP4 freeform atoms
                    audio_file[format_key] = [value.encode('utf-8')]
                else:
                    # FLAC and other formats
                    audio_file[format_key] = [value]
    
    def batch_write_metadata(self, metadata_dict: Dict[str, Dict[str, Any]], 
                           backup: bool = True) -> Dict[str, bool]:
        """
        Write metadata to multiple files.
        
        Args:
            metadata_dict: Dictionary mapping file paths to metadata
            backup: Whether to create backups
            
        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        
        for file_path, metadata in metadata_dict.items():
            if 'error' in metadata:
                results[file_path] = False
                continue
                
            success = self.write_metadata(file_path, metadata, backup)
            results[file_path] = success
        
        return results