"""
Abstract interfaces for metadata processing components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from .models import AudioMetadata, AudioFileInfo, MetadataSearchResult, ProcessingResult


class MetadataExtractorInterface(ABC):
    """Interface for metadata extraction from audio files."""
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> AudioMetadata:
        """Extract metadata from an audio file."""
        pass
    
    @abstractmethod
    def extract_file_info(self, file_path: Path) -> AudioFileInfo:
        """Extract technical file information."""
        pass
    
    @abstractmethod
    def supports_format(self, file_format: str) -> bool:
        """Check if format is supported."""
        pass


class MetadataWriterInterface(ABC):
    """Interface for writing metadata to audio files."""
    
    @abstractmethod
    def write_metadata(self, file_path: Path, metadata: AudioMetadata, 
                      create_backup: bool = True) -> ProcessingResult:
        """Write metadata to an audio file."""
        pass
    
    @abstractmethod
    def supports_format(self, file_format: str) -> bool:
        """Check if format is supported for writing."""
        pass
    
    @abstractmethod
    def validate_metadata(self, metadata: AudioMetadata, file_format: str) -> List[str]:
        """Validate metadata for a specific format."""
        pass


class MetadataParserInterface(ABC):
    """Interface for parsing metadata from various sources."""
    
    @abstractmethod
    def parse(self, source: Any) -> Optional[AudioMetadata]:
        """Parse metadata from source."""
        pass
    
    @abstractmethod
    def can_parse(self, source: Any) -> bool:
        """Check if parser can handle this source."""
        pass


class MetadataSearchInterface(ABC):
    """Interface for searching metadata from external sources."""
    
    @abstractmethod
    def search_metadata(self, query_metadata: AudioMetadata, 
                       max_results: int = 10) -> List[MetadataSearchResult]:
        """Search for metadata matches."""
        pass
    
    @abstractmethod
    def get_detailed_metadata(self, identifier: str) -> Optional[AudioMetadata]:
        """Get detailed metadata by identifier."""
        pass


class MetadataValidatorInterface(ABC):
    """Interface for validating metadata."""
    
    @abstractmethod
    def validate(self, metadata: AudioMetadata) -> List[str]:
        """Validate metadata and return list of issues."""
        pass
    
    @abstractmethod
    def is_valid(self, metadata: AudioMetadata) -> bool:
        """Check if metadata is valid."""
        pass


class MetadataServiceInterface(ABC):
    """Interface for the main metadata processing service."""
    
    @abstractmethod
    def process_file(self, file_path: Path, write_metadata: bool = False) -> ProcessingResult:
        """Process a single audio file."""
        pass
    
    @abstractmethod
    def process_batch(self, file_paths: List[Path], 
                     write_metadata: bool = False) -> Dict[str, ProcessingResult]:
        """Process multiple audio files."""
        pass