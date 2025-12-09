"""
Mutagen-based metadata writer.
"""

import logging
import shutil
from pathlib import Path
from typing import List

try:
    import mutagen
    from mutagen.flac import FLAC
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from ..core.interfaces import MetadataWriterInterface
    # AudioMetadata, ProcessingResult hold logical metadata + result state
from ..core.models import AudioMetadata, ProcessingResult
from ..core.exceptions import MetadataWriteError

logger = logging.getLogger(__name__)


class MutagenWriter(MetadataWriterInterface):
    """Metadata writer using Mutagen library."""

    def __init__(self):
        if not MUTAGEN_AVAILABLE:
            raise ImportError("Mutagen library is required for metadata writing")

        # Format mappings
        self.format_mappings = {
            'flac': {
                'title': 'TITLE',
                'artist': 'ARTIST',
                'album': 'ALBUM',
                'date': 'DATE',
                'genre': 'GENRE',
                'track_number': 'TRACKNUMBER',
                'album_artist': 'ALBUMARTIST',
                'composer': 'COMPOSER',
            },
            'mp3': {
                'title': 'TIT2',
                'artist': 'TPE1',
                'album': 'TALB',
                'date': 'TDRC',
                'genre': 'TCON',
                'track_number': 'TRCK',
                'album_artist': 'TPE2',
                'composer': 'TCOM',
            },
            'mp4': {
                'title': '\xa9nam',
                'artist': '\xa9ART',
                'album': '\xa9alb',
                'date': '\xa9day',
                'genre': '\xa9gen',
                'track_number': 'trkn',
                'album_artist': 'aART',
                'composer': '\xa9wrt',
            },
        }

        self.supported_formats = {'flac', 'mp3', 'mp4', 'ogg'}

    def write_metadata(
        self,
        file_path: Path,
        metadata: AudioMetadata,
        create_backup: bool = True,
    ) -> ProcessingResult:
        """Write metadata to an audio file."""
        # Normalize to Path in case a string was passed
        file_path = Path(file_path)

        if not file_path.exists():
            return ProcessingResult(
                success=False,
                error=f"File not found: {file_path}",
            )

        backup_path: Path | None = None
        try:
            # Create backup if requested
            if create_backup:
                backup_path = self._create_backup(file_path)

            # Load the audio file
            audio_file = mutagen.File(str(file_path))
            if audio_file is None:
                return ProcessingResult(
                    success=False,
                    error=f"Could not load audio file: {file_path}",
                )

            # Detect format and validate
            file_format = self._detect_format(audio_file)
            if not self.supports_format(file_format):
                return ProcessingResult(
                    success=False,
                    error=f"Unsupported format: {file_format}",
                )

            # Validate metadata
            validation_errors = self.validate_metadata(metadata, file_format)

            # Write metadata
            success = self._write_by_format(audio_file, file_format, metadata)

            if success:
                audio_file.save()
                logger.info(f"Metadata written successfully to: {file_path}")

                result = ProcessingResult(success=True, metadata=metadata)
                if validation_errors:
                    for error in validation_errors:
                        result.add_warning(f"Validation warning: {error}")
                return result
            else:
                return ProcessingResult(
                    success=False,
                    error="Failed to write metadata to file",
                )

        except Exception as e:
            logger.error(f"Error writing metadata to {file_path}: {e}")
            # backup_path may be None; that’s fine for the exception type
            raise MetadataWriteError(
                f"Write operation failed: {e}",
                str(file_path),
                backup_path,
            )

    def supports_format(self, file_format: str) -> bool:
        """Check if format is supported for writing."""
        return file_format.lower() in self.supported_formats

    def validate_metadata(
        self,
        metadata: AudioMetadata,
        file_format: str,
    ) -> List[str]:
        """Validate metadata for a specific format."""
        errors: List[str] = []

        # Check for format-specific limitations
        if file_format == 'mp3':
            # MP3 has character encoding limitations
            for field in ['title', 'artist', 'album']:
                value = getattr(metadata, field, None)
                if value and len(value.encode('utf-8')) > 255:
                    errors.append(f"{field} too long for MP3 format")

        elif file_format == 'mp4':
            # MP4 has specific requirements for track numbers
            if metadata.track_number:
                try:
                    int(metadata.track_number)
                except ValueError:
                    errors.append("track_number must be numeric for MP4 format")

        return errors

    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of the original file."""
        file_path = Path(file_path)
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.warning(f"Could not create backup for {file_path}: {e}")
            raise MetadataWriteError(
                f"Backup creation failed: {e}",
                str(file_path),
            )

    def _detect_format(self, audio_file) -> str:
        """Detect the audio file format."""
        if audio_file is None:
            return 'unknown'

        format_mapping = {
            'FLAC': 'flac',
            'MP3': 'mp3',
            'MP4': 'mp4',
            'OggVorbis': 'ogg',
        }

        file_type = type(audio_file).__name__
        return format_mapping.get(file_type, 'unknown')

    def _write_by_format(
        self,
        audio_file,
        file_format: str,
        metadata: AudioMetadata,
    ) -> bool:
        """Write metadata based on file format."""
        if file_format not in self.format_mappings:
            logger.warning(f"No format mapping available for: {file_format}")
            return False

        mapping = self.format_mappings[file_format]

        try:
            for standard_key, format_key in mapping.items():
                value = getattr(metadata, standard_key, None)
                if value is not None and value != '':
                    # Handle special cases
                    if format_key == 'trkn' and file_format == 'mp4':
                        # MP4 track numbers are stored as tuples
                        try:
                            track_num = int(value)
                            audio_file[format_key] = [(track_num, 0)]
                        except ValueError:
                            logger.warning(
                                f"Invalid track number for MP4: {value}",
                            )
                            continue
                    else:
                        # Standard string metadata
                        if isinstance(value, list):
                            audio_file[format_key] = value
                        else:
                            audio_file[format_key] = [str(value)]

            # Add MusicBrainz IDs if available
            mb_mappings = {
                'musicbrainz_recording_id': 'MUSICBRAINZ_TRACKID',
                'musicbrainz_release_id': 'MUSICBRAINZ_ALBUMID',
                'musicbrainz_artist_id': 'MUSICBRAINZ_ARTISTID',
            }

            for standard_key, format_key in mb_mappings.items():
                value = getattr(metadata, standard_key, None)
                if value:
                    audio_file[format_key] = [str(value)]

            return True

        except Exception as e:
            logger.error(f"Error writing metadata: {e}")
            return False
