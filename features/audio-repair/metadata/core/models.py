"""
Data models for metadata processing.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import datetime


@dataclass
class AudioFileInfo:
    """Information about an audio file."""
    file_path: Path
    file_format: str
    file_size: int
    duration: float
    bitrate: int
    sample_rate: int
    channels: int
    bits_per_sample: int = 0


@dataclass
class AudioMetadata:
    """Complete audio metadata model."""
    # Core metadata fields
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    date: Optional[str] = None
    genre: Optional[str] = None
    track_number: Optional[str] = None
    disc_number: Optional[str] = None
    total_tracks: Optional[str] = None
    total_discs: Optional[str] = None
    
    # Extended metadata
    composer: Optional[str] = None
    performer: Optional[str] = None
    conductor: Optional[str] = None
    label: Optional[str] = None
    catalog_number: Optional[str] = None
    isrc: Optional[str] = None
    
    # MusicBrainz identifiers
    musicbrainz_track_id: Optional[str] = None
    musicbrainz_recording_id: Optional[str] = None
    musicbrainz_release_id: Optional[str] = None
    musicbrainz_artist_id: Optional[str] = None
    
    # File information
    file_info: Optional[AudioFileInfo] = None
    
    # Processing metadata
    source: str = "unknown"  # Source of metadata (embedded, filename, musicbrainz)
    confidence: float = 0.0  # Confidence score for metadata accuracy
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if field_value is not None:
                if isinstance(field_value, Path):
                    result[field_name] = str(field_value)
                elif isinstance(field_value, datetime.datetime):
                    result[field_name] = field_value.isoformat()
                elif isinstance(field_value, AudioFileInfo):
                    result['file_info'] = field_value.__dict__.copy()
                    if 'file_path' in result['file_info']:
                        result['file_info']['file_path'] = str(result['file_info']['file_path'])
                else:
                    result[field_name] = field_value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioMetadata':
        """Create from dictionary."""
        # Handle file_info separately
        file_info_data = data.pop('file_info', None)
        file_info = None
        if file_info_data:
            if 'file_path' in file_info_data:
                file_info_data['file_path'] = Path(file_info_data['file_path'])
            file_info = AudioFileInfo(**file_info_data)
        
        # Handle datetime fields
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.datetime.fromisoformat(data['last_updated'])
        
        # Create instance
        metadata = cls(**data)
        metadata.file_info = file_info
        return metadata
    
    def get_missing_fields(self, required_fields: List[str] = None) -> List[str]:
        """Get list of missing required fields."""
        if required_fields is None:
            required_fields = ['title', 'artist', 'album', 'date', 'genre', 'track_number']
        
        missing = []
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and value.strip() == ''):
                missing.append(field)
        
        return missing
    
    def is_complete(self, required_fields: List[str] = None) -> bool:
        """Check if metadata is complete."""
        return len(self.get_missing_fields(required_fields)) == 0
    
    def merge(self, other: 'AudioMetadata', prefer_existing: bool = True) -> 'AudioMetadata':
        """Merge with another metadata object."""
        merged = AudioMetadata()
        
        for field_name in self.__dataclass_fields__:
            if field_name in ['last_updated', 'file_info']:  # Skip special fields
                continue
                
            current_value = getattr(self, field_name)
            other_value = getattr(other, field_name)
            
            if prefer_existing and current_value:
                merged_value = current_value
            elif other_value:
                merged_value = other_value
            else:
                merged_value = current_value
                
            setattr(merged, field_name, merged_value)
        
        # Handle special fields
        merged.file_info = self.file_info or other.file_info
        merged.last_updated = max(self.last_updated, other.last_updated)
        merged.confidence = max(self.confidence, other.confidence)
        
        return merged


@dataclass
class MetadataSearchResult:
    """Result from a metadata search."""
    metadata: AudioMetadata
    confidence_score: float
    source: str
    match_details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Update metadata with search result info."""
        self.metadata.confidence = self.confidence_score
        self.metadata.source = self.source


@dataclass
class ProcessingResult:
    """Result of metadata processing operation."""
    success: bool
    metadata: Optional[AudioMetadata] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)