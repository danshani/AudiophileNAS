"""
Main metadata processing service orchestrating all operations.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
import time

from ..core.interfaces import MetadataServiceInterface
from ..core.models import AudioMetadata, ProcessingResult
from ..core.exceptions import MetadataProcessingError, FileProcessingError

from .file_service import FileService
from .musicbrainz_service import MusicBrainzService

logger = logging.getLogger(__name__)


class MetadataService(MetadataServiceInterface):
    """
    Main service for orchestrating metadata processing operations.
    
    This service coordinates between file operations, parsing, searching,
    and writing metadata using a clean separation of concerns.
    """
    
    def __init__(self, file_service: FileService = None, 
                 musicbrainz_service: MusicBrainzService = None):
        """
        Initialize the metadata service.
        
        Args:
            file_service: Service for file operations
            musicbrainz_service: Service for MusicBrainz operations
        """
        self.file_service = file_service or FileService()
        self.musicbrainz_service = musicbrainz_service or MusicBrainzService()
        
    def process_file(self, file_path: Path, write_metadata: bool = False) -> ProcessingResult:
        """
        Process a single audio file to complete its metadata.
        
        Args:
            file_path: Path to the audio file
            write_metadata: Whether to write completed metadata back to file
            
        Returns:
            ProcessingResult with success status and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Step 1: Extract existing metadata
            current_metadata = self.file_service.extract_metadata(file_path)
            if not current_metadata:
                return ProcessingResult(
                    success=False,
                    error=f"Could not extract metadata from: {file_path}"
                )
            
            logger.debug(f"Current metadata: {current_metadata.to_dict()}")
            
            # Step 2: Check if metadata is already complete
            missing_fields = current_metadata.get_missing_fields()
            if not missing_fields:
                logger.info(f"Metadata already complete for: {file_path}")
                result = ProcessingResult(success=True, metadata=current_metadata)
                result.processing_time = time.time() - start_time
                return result
            
            logger.info(f"Missing fields: {missing_fields}")
            
            # Step 3: Try filename parsing if no searchable metadata
            if not self._has_searchable_metadata(current_metadata):
                logger.info("No searchable metadata found, attempting filename parsing")
                filename_metadata = self.file_service.parse_filename(file_path)
                if filename_metadata:
                    logger.info(f"Extracted from filename: {filename_metadata.to_dict()}")
                    current_metadata = current_metadata.merge(filename_metadata, prefer_existing=True)
            
            # Step 4: Search for missing metadata using MusicBrainz
            completed_metadata = self._complete_metadata_from_musicbrainz(current_metadata)
            
            # Step 5: Write metadata back to file if requested
            if write_metadata and completed_metadata:
                write_result = self.file_service.write_metadata(file_path, completed_metadata)
                if not write_result.success:
                    result = ProcessingResult(
                        success=False,
                        metadata=completed_metadata,
                        error=f"Failed to write metadata: {write_result.error}"
                    )
                    result.processing_time = time.time() - start_time
                    return result
            
            # Step 6: Return results
            result = ProcessingResult(
                success=True,
                metadata=completed_metadata or current_metadata
            )
            result.processing_time = time.time() - start_time
            
            if completed_metadata:
                logger.info(f"Metadata completed for: {file_path}")
            else:
                logger.warning(f"No suitable match found for: {file_path}")
                result.add_warning("No suitable metadata match found")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            result = ProcessingResult(
                success=False,
                error=str(e)
            )
            result.processing_time = time.time() - start_time
            return result
    
    def process_batch(self, file_paths: List[Path], 
                     write_metadata: bool = False) -> Dict[str, ProcessingResult]:
        """
        Process multiple audio files.
        
        Args:
            file_paths: List of file paths to process
            write_metadata: Whether to write metadata back to files
            
        Returns:
            Dictionary mapping file paths to processing results
        """
        results = {}
        total_files = len(file_paths)
        
        logger.info(f"Processing {total_files} files")
        
        for i, file_path in enumerate(file_paths, 1):
            logger.info(f"Processing {i}/{total_files}: {file_path.name}")
            result = self.process_file(file_path, write_metadata)
            results[str(file_path)] = result
            
        # Log summary
        successful = sum(1 for r in results.values() if r.success)
        logger.info(f"Batch processing complete: {successful}/{total_files} successful")
        
        return results
    
    def _has_searchable_metadata(self, metadata: AudioMetadata) -> bool:
        """Check if metadata has enough information for searching."""
        return any(getattr(metadata, field) for field in ['title', 'artist', 'album'])
    
    def _complete_metadata_from_musicbrainz(self, metadata: AudioMetadata) -> Optional[AudioMetadata]:
        """Complete metadata using MusicBrainz search."""
        try:
            search_results = self.musicbrainz_service.search_metadata(metadata)
            
            if not search_results:
                return None
                
            # Get the best match
            best_match = search_results[0]
            logger.info(f"Best match: '{best_match.metadata.title}' (score: {best_match.confidence_score})")
            
            # Merge with current metadata
            completed_metadata = metadata.merge(best_match.metadata, prefer_existing=True)
            completed_metadata.confidence = best_match.confidence_score
            completed_metadata.source = f"{metadata.source}+musicbrainz"
            
            return completed_metadata
            
        except Exception as e:
            logger.error(f"Error searching MusicBrainz: {e}")
            return None