"""
Filename parser to extract metadata from audio filenames.
This helps when audio files have no embedded metadata but contain 
information in their filename structure.
"""

import os
import re
from pathlib import Path
from typing import Optional, Any
import logging

from ..core.interfaces import MetadataParserInterface
from ..core.models import AudioMetadata

logger = logging.getLogger(__name__)

class FilenameParser(MetadataParserInterface):
    """Parse metadata from audio filenames."""
    
    def __init__(self):
        # Common filename patterns
        self.patterns = [
            # Pattern: "01 Artist_-_Track.ext" or "01 Artist - Track.ext"
            r'^(\d+)[\s\.]*([^_\-]+?)[\s]*[-_]+[\s]*(.+?)(?:\.[^.]+)?$',
            
            # Pattern: "Track - Artist.ext"
            r'^(.+?)[\s]*-[\s]*(.+?)(?:\.[^.]+)?$',
            
            # Pattern: "Artist - Album - Track.ext" 
            r'^(.+?)[\s]*-[\s]*(.+?)[\s]*-[\s]*(.+?)(?:\.[^.]+)?$',
            
            # Pattern: "Artist - Track (Album).ext"
            r'^(.+?)[\s]*-[\s]*(.+?)[\s]*\((.+?)\)(?:\.[^.]+)?$',
            
            # Pattern: "Track Number - Artist - Track Name.ext"
            r'^(\d+)[\s\-\.]*(.+?)[\s]*-[\s]*(.+?)(?:\.[^.]+)?$',
            
            # Pattern: "Track Number. Track Name.ext" 
            r'^(\d+)\.[\s]*(.+?)(?:\.[^.]+)?$',
        ]
    
    def parse(self, source: Any) -> Optional[AudioMetadata]:
        """Parse metadata from filename."""
        if isinstance(source, (str, Path)):
            return self.parse_filename(source)
        return None
    
    def can_parse(self, source: Any) -> bool:
        """Check if parser can handle this source."""
        return isinstance(source, (str, Path))
    
    def parse_filename(self, filepath: Any) -> Optional[AudioMetadata]:
        """
        Parse metadata from filename.
        
        Args:
            filepath: Path to the audio file
            
        Returns:
            AudioMetadata with extracted information
        """
        if isinstance(filepath, Path):
            filepath = str(filepath)
            
        filename = os.path.basename(filepath)
        name_without_ext = os.path.splitext(filename)[0]
        
        logger.debug(f"Parsing filename: {filename}")
        
        # Try each pattern
        for i, pattern in enumerate(self.patterns):
            match = re.match(pattern, name_without_ext, re.IGNORECASE)
            if match:
                metadata = self._extract_metadata_from_match(match, i, name_without_ext)
                if metadata:
                    logger.info(f"Parsed filename '{filename}' using pattern {i+1}: {metadata}")
                    return metadata
        
        # If no pattern matches, try to extract basic info
        basic_metadata = self._extract_basic_metadata(name_without_ext)
        if basic_metadata:
            logger.info(f"Extracted basic metadata from '{filename}': {basic_metadata}")
            return basic_metadata
        
        logger.warning(f"Could not parse metadata from filename: {filename}")
        return None
    
    def _extract_metadata_from_match(self, match, pattern_index: int, filename: str) -> Optional[AudioMetadata]:
        """Extract metadata based on the matched pattern."""
        groups = match.groups()
        metadata = AudioMetadata(source="filename")
        
        try:
            if pattern_index == 0:  # "01 Artist_-_Track.ext"
                track_num, artist, title = groups
                metadata.track_number = track_num.strip().zfill(2)
                metadata.artist = self._clean_text(artist)
                metadata.title = self._clean_text(title)
                
            elif pattern_index == 1:  # "Track - Artist.ext"
                title, artist = groups
                metadata.title = self._clean_text(title)
                metadata.artist = self._clean_text(artist)
                
            elif pattern_index == 2:  # "Artist - Album - Track.ext"
                artist, album, title = groups
                metadata.artist = self._clean_text(artist)
                metadata.album = self._clean_text(album)
                metadata.title = self._clean_text(title)
                
            elif pattern_index == 3:  # "Artist - Track (Album).ext"
                artist, title, album = groups
                metadata.artist = self._clean_text(artist)
                metadata.title = self._clean_text(title)
                metadata.album = self._clean_text(album)
                
            elif pattern_index == 4:  # "Track Number - Artist - Track Name.ext"
                track_num, artist, title = groups
                metadata.track_number = track_num.strip().zfill(2)
                metadata.artist = self._clean_text(artist)
                metadata.title = self._clean_text(title)
                
            elif pattern_index == 5:  # "Track Number. Track Name.ext"
                track_num, title = groups
                metadata.track_number = track_num.strip().zfill(2)
                metadata.title = self._clean_text(title)
        
        except (IndexError, ValueError) as e:
            logger.warning(f"Error extracting metadata from pattern {pattern_index}: {e}")
            return None
        
        # Additional processing for special cases
        metadata = self._post_process_metadata(metadata, filename)
        
        return metadata
    
    def _extract_basic_metadata(self, filename: str) -> Optional[AudioMetadata]:
        """Extract basic metadata when no pattern matches."""
        metadata = AudioMetadata(source="filename")
        
        # Try to extract track number from beginning
        track_match = re.match(r'^(\d+)', filename)
        if track_match:
            metadata.track_number = track_match.group(1).zfill(2)
            # Remove track number from filename for title
            remaining = re.sub(r'^\d+[\s\.\-_]*', '', filename)
            if remaining:
                metadata.title = self._clean_text(remaining)
        else:
            # Use entire filename as title
            metadata.title = self._clean_text(filename)
        
        return metadata
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text fields."""
        if not text:
            return ""
        
        # Fix common character encoding corruptions
        text = self._fix_character_encoding(text)
        
        # Remove common separators and clean up
        text = text.replace('_-_', ' - ').replace('_', ' ').replace('--', '-')
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove leading/trailing dashes and dots
        text = re.sub(r'^[\-\.\s]+|[\-\.\s]+$', '', text)
        
        return text
    
    def _fix_character_encoding(self, text: str) -> str:
        """Fix common character encoding corruptions in filenames."""
        # Common character encoding corruptions found in filenames
        # Based on analysis: ä (U+00E4) becomes Г (U+0413) + ¤ (U+00A4)
        corruptions = {
            'Г¤': 'ä',  # ä (a-umlaut) - confirmed pattern
            'Г¶': 'ö',  # ö (o-umlaut) 
            'Г¼': 'ü',  # ü (u-umlaut)
            'Г„': 'Ä',  # Ä (A-umlaut)
            'Г–': 'Ö',  # Ö (O-umlaut)
            'Гњ': 'Ü',  # Ü (U-umlaut)
            'ГџÂ': 'ß', # ß (sharp s)
            'Гџ': 'ß',  # ß (sharp s)
            'Г©': 'é',  # é (e-acute)
            'Г¡': 'á',  # á (a-acute) 
            'Г­': 'í',  # í (i-acute)
            'Гі': 'ó',  # ó (o-acute)
            'Гє': 'ú',  # ú (u-acute)
            'Г±': 'ñ',  # ñ (n-tilde)
            'Г§': 'ç',  # ç (c-cedilla)
            'â€™': "'", # right single quotation mark
            'â€œ': '"', # left double quotation mark
            'â€': '"',  # right double quotation mark
            'â€"': '–', # en dash
            'â€"': '—', # em dash
        }
        
        for corrupted, correct in corruptions.items():
            text = text.replace(corrupted, correct)
        
        return text
    
    def _post_process_metadata(self, metadata: AudioMetadata, filename: str) -> AudioMetadata:
        """Post-process extracted metadata for better results."""
        
        # Handle special artist name formatting (like "Shiwa 2000")
        if metadata.artist:
            artist = metadata.artist
            # Fix common formatting issues
            artist = re.sub(r'\s*2000\s*', ' 2000', artist)  # Normalize "Shiwa2000" to "Shiwa 2000"
            metadata.artist = artist.strip()
        
        # Handle special title formatting
        if metadata.title:
            title = metadata.title
            # Remove file format indicators
            title = re.sub(r'\.(flac|mp3|wav|m4a|ogg)$', '', title, re.IGNORECASE)
            metadata.title = title.strip()
        
        # Try to extract additional info from complex filenames
        if metadata.artist and metadata.title:
            # Look for album info in parentheses or brackets
            full_text = filename
            album_match = re.search(r'[\[\(]([^[\]()]+)[\]\)]', full_text)
            if album_match and not metadata.album:
                potential_album = self._clean_text(album_match.group(1))
                # Only use if it doesn't look like year or format info
                if not re.match(r'^\d{4}$', potential_album) and potential_album.lower() not in ['flac', 'mp3', 'wav']:
                    metadata.album = potential_album
        
        return metadata
    
    def can_parse_filename(self, filepath: str) -> bool:
        """
        Check if a filename can be parsed for metadata.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if filename appears parseable
        """
        filename = os.path.basename(filepath)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Check if filename has structured information
        has_track_number = bool(re.match(r'^\d+', name_without_ext))
        has_separators = any(sep in name_without_ext for sep in ['-', '_', ' - '])
        has_reasonable_length = len(name_without_ext) > 5
        
        return has_track_number or has_separators or has_reasonable_length
    
    def normalize_for_search(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize metadata for better MusicBrainz search results.
        
        Args:
            metadata: Extracted metadata
            
        Returns:
            Normalized metadata for searching
        """
        normalized = metadata.copy()
        
        # Normalize artist names for better matching
        if 'artist' in normalized:
            artist = normalized['artist']
            # Common normalizations
            artist = re.sub(r'\s+', ' ', artist)  # Multiple spaces to single
            artist = artist.strip()
            normalized['artist'] = artist
        
        # Normalize titles
        if 'title' in normalized:
            title = normalized['title']
            # Remove common prefixes/suffixes that might interfere with search
            title = re.sub(r'^\d+[\.\s]*', '', title)  # Remove track number prefix
            title = re.sub(r'\s+', ' ', title).strip()
            normalized['title'] = title
        
        return normalized