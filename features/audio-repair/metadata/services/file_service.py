"""
File service for handling audio file operations.
"""

import logging
from pathlib import Path
from typing import Optional, List

from ..core.interfaces import MetadataExtractorInterface, MetadataWriterInterface, MetadataParserInterface
from ..core.models import AudioMetadata, AudioFileInfo, ProcessingResult
from ..core.exceptions import FileProcessingError, MetadataParsingError

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for file-related metadata operations.
    
    Coordinates between extractors, parsers, and writers to handle
    all file-based metadata operations.
    """
    
    def __init__(self, 
                 extractor: MetadataExtractorInterface = None,
                 writer: MetadataWriterInterface = None,
                 filename_parser: MetadataParserInterface = None):
        """
        Initialize file service with pluggable components.
        
        Args:
            extractor: Metadata extractor implementation
            writer: Metadata writer implementation  
            filename_parser: Filename parser implementation
        """
        # Import here to avoid circular dependencies
        if extractor is None:
            from ..parsers.metadata_parser import MetadataExtractor
            extractor = MetadataExtractor()
            
        if writer is None:
            from ..writers.mutagen_writer import MutagenWriter
            writer = MutagenWriter()
            
        if filename_parser is None:
            from ..parsers.filename_parser import FilenameParser
            filename_parser = FilenameParser()
        
        self.extractor = extractor
        self.writer = writer
        self.filename_parser = filename_parser
    
    def extract_metadata(self, file_path: Path) -> Optional[AudioMetadata]:
        """
        Extract metadata from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            AudioMetadata object or None if extraction failed
        """
        try:
            return self.extractor.extract_metadata(file_path)
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
            raise FileProcessingError(f"Metadata extraction failed: {e}", str(file_path), "extract")
    
    def extract_file_info(self, file_path: Path) -> Optional[AudioFileInfo]:
        """
        Extract technical file information.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            AudioFileInfo object or None if extraction failed
        """
        try:
            return self.extractor.extract_file_info(file_path)
        except Exception as e:
            logger.error(f"Failed to extract file info from {file_path}: {e}")
            raise FileProcessingError(f"File info extraction failed: {e}", str(file_path), "extract_info")
    
    def parse_filename(self, file_path: Path) -> Optional[AudioMetadata]:
        """
        Parse metadata from filename.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            AudioMetadata parsed from filename or None
        """
        try:
            if self.filename_parser.can_parse(file_path):
                return self.filename_parser.parse(file_path)
            return None
        except Exception as e:
            logger.error(f"Failed to parse filename {file_path}: {e}")
            raise MetadataParsingError(f"Filename parsing failed: {e}", "filename", str(file_path))
    
    def write_metadata(self, file_path: Path, metadata: AudioMetadata, 
                      create_backup: bool = True) -> ProcessingResult:
        """
        Write metadata to an audio file.
        
        Args:
            file_path: Path to the audio file
            metadata: Metadata to write
            create_backup: Whether to create backup before writing
            
        Returns:
            ProcessingResult indicating success or failure
        """
        try:
            return self.writer.write_metadata(file_path, metadata, create_backup)
        except Exception as e:
            logger.error(f"Failed to write metadata to {file_path}: {e}")
            return ProcessingResult(
                success=False,
                error=f"Write operation failed: {e}"
            )
    
    def validate_file(self, file_path: Path) -> bool:
        """
        Validate that file exists and is a supported audio format.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if file is valid and supported
        """
        if not file_path.exists():
            return False
            
        if not file_path.is_file():
            return False
            
        # Check if format is supported
        file_format = self._detect_format(file_path)
        return self.extractor.supports_format(file_format)
    
    def find_audio_files(self, directory: Path, 
                        extensions: List[str] = None,
                        recursive: bool = True) -> List[Path]:
        """
        Find audio files in directory.
        
        Args:
            directory: Directory to search
            extensions: File extensions to look for
            recursive: Whether to search subdirectories
            
        Returns:
            List of audio file paths
        """
        if extensions is None:
            extensions = ['.flac', '.mp3', '.m4a', '.ogg', '.wav']
        
        extensions = [ext.lower() for ext in extensions]
        audio_files = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
            
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                if self.validate_file(file_path):
                    audio_files.append(file_path)
        
        return audio_files
    
    def _detect_format(self, file_path: Path) -> str:
        """Detect audio format from file extension."""
        suffix = file_path.suffix.lower()
        format_mapping = {
            '.flac': 'flac',
            '.mp3': 'mp3', 
            '.m4a': 'mp4',
            '.mp4': 'mp4',
            '.ogg': 'ogg',
            '.wav': 'wav'
        }
        return format_mapping.get(suffix, 'unknown')