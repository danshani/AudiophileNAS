"""
Metadata completer that uses MusicBrainz API to fill missing metadata.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher

from .musicbrainz_client import MusicBrainzClient
from .metadata_extractor import MetadataExtractor
from .filename_parser import FilenameParser
from .config import METADATA_CONFIG

logger = logging.getLogger(__name__)

class MetadataCompleter:
    """Complete missing metadata using MusicBrainz API."""
    
    def __init__(self):
        self.mb_client = MusicBrainzClient()
        self.extractor = MetadataExtractor()
        self.filename_parser = FilenameParser()
        self.search_threshold = METADATA_CONFIG['search_threshold']
        self.max_results = METADATA_CONFIG['max_search_results']
        self.fuzzy_matching = METADATA_CONFIG['fuzzy_matching']
    
    def complete_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Complete metadata for an audio file using MusicBrainz.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary with completed metadata
        """
        # Extract current metadata
        current_metadata = self.extractor.extract_metadata(file_path)
        logger.info(f"Current metadata for {os.path.basename(file_path)}: {current_metadata}")
        
        # If no useful metadata exists, try to parse from filename
        has_searchable_metadata = any(current_metadata.get(field) for field in ['title', 'artist', 'album'])
        if not has_searchable_metadata:
            logger.info(f"No searchable metadata found, attempting filename parsing for: {file_path}")
            filename_metadata = self.filename_parser.parse_filename(file_path)
            if filename_metadata:
                logger.info(f"Extracted from filename: {filename_metadata}")
                # Merge filename metadata into current metadata
                for key, value in filename_metadata.items():
                    if key not in current_metadata or not current_metadata[key]:
                        current_metadata[key] = value
        
        # Check what's missing
        missing_fields = self.extractor.get_missing_metadata_fields(current_metadata)
        if not missing_fields:
            logger.info(f"Metadata already complete for: {file_path}")
            return current_metadata
        
        logger.info(f"Missing fields: {missing_fields}")
        
        # Search MusicBrainz for matches
        matches = self._search_musicbrainz(current_metadata)
        if not matches:
            logger.warning(f"No MusicBrainz matches found for: {file_path}")
            return current_metadata
        
        # Find best match and complete metadata
        best_match = self._find_best_match(current_metadata, matches)
        if best_match:
            completed_metadata = self._merge_metadata(current_metadata, best_match)
            logger.info(f"Metadata completed for: {file_path}")
            return completed_metadata
        else:
            logger.warning(f"No suitable match found for: {file_path}")
            return current_metadata
    
    def _search_musicbrainz(self, metadata: Dict[str, Any]) -> List[Dict]:
        """Search MusicBrainz for potential matches."""
        matches = []
        
        # Try different search strategies
        if 'title' in metadata:
            title = metadata['title']
            artist = metadata.get('artist', '')
            album = metadata.get('album', '')
            
            # Strategy 1: Search with title, artist, and album
            if artist and album:
                logger.info(f"Searching with title='{title}', artist='{artist}', album='{album}'")
                results = self.mb_client.search_by_metadata(
                    title=title, artist=artist, album=album, limit=self.max_results
                )
                matches.extend(results)
            
            # Strategy 2: Search with title and artist only
            if artist and not matches:
                logger.info(f"Searching with title='{title}', artist='{artist}'")
                results = self.mb_client.search_by_metadata(
                    title=title, artist=artist, limit=self.max_results
                )
                matches.extend(results)
            
            # Strategy 3: Search with title only
            if not matches:
                logger.info(f"Searching with title='{title}' only")
                results = self.mb_client.search_recordings(
                    f'recording:"{title}"', limit=self.max_results
                )
                matches.extend(results)
        
        logger.info(f"Found {len(matches)} potential matches")
        return matches
    
    def _find_best_match(self, current_metadata: Dict[str, Any], 
                        matches: List[Dict]) -> Optional[Dict]:
        """Find the best match from MusicBrainz results."""
        best_match = None
        best_score = 0
        
        for match in matches:
            score = self._calculate_match_score(current_metadata, match)
            logger.debug(f"Match score: {score} for '{match.get('title', 'Unknown')}'")
            
            if score > best_score and score >= self.search_threshold:
                best_score = score
                best_match = match
        
        if best_match:
            logger.info(f"Best match: '{best_match.get('title', 'Unknown')}' (score: {best_score})")
        
        return best_match
    
    def _calculate_match_score(self, current: Dict[str, Any], candidate: Dict) -> float:
        """Calculate similarity score between current metadata and candidate."""
        score = 0.0
        total_weight = 0.0
        
        # Field weights for scoring
        weights = {
            'title': 3.0,
            'artist': 2.0,
            'album': 2.0,
            'date': 1.0,
            'genre': 0.5
        }
        
        # Track which fields we actually have to compare
        compared_fields = 0
        
        for field, weight in weights.items():
            current_value = current.get(field, '').lower().strip()
            
            if field == 'artist' and 'artist-credit' in candidate:
                # Handle MusicBrainz artist-credit format
                candidate_value = self._extract_artist_name(candidate['artist-credit']).lower().strip()
            elif field == 'album' and 'releases' in candidate:
                # Get album name from releases
                candidate_value = self._extract_album_name(candidate['releases']).lower().strip()
            elif field == 'date' and 'releases' in candidate:
                # Get release date
                candidate_value = self._extract_release_date(candidate['releases'])
            else:
                candidate_value = candidate.get(field, '').lower().strip()
            
            # Only score fields where we have current data to compare
            if current_value and candidate_value:
                if self.fuzzy_matching:
                    similarity = SequenceMatcher(None, current_value, candidate_value).ratio()
                else:
                    similarity = 1.0 if current_value == candidate_value else 0.0
                
                score += similarity * weight
                total_weight += weight
                compared_fields += 1
            elif current_value and not candidate_value:
                # Penalize if we have data but candidate doesn't
                total_weight += weight
        
        # For filename-parsed metadata, be more lenient if we have good matches on core fields
        if compared_fields >= 2:  # If we compared at least 2 fields
            core_fields = ['title', 'artist']
            core_matches = 0
            core_total = 0
            
            for field in core_fields:
                current_value = current.get(field, '').lower().strip()
                
                if field == 'artist' and 'artist-credit' in candidate:
                    candidate_value = self._extract_artist_name(candidate['artist-credit']).lower().strip()
                else:
                    candidate_value = candidate.get(field, '').lower().strip()
                
                if current_value and candidate_value:
                    if self.fuzzy_matching:
                        similarity = SequenceMatcher(None, current_value, candidate_value).ratio()
                    else:
                        similarity = 1.0 if current_value == candidate_value else 0.0
                    
                    core_matches += similarity
                    core_total += 1
            
            # If core fields match well, boost the overall score
            if core_total > 0:
                core_score = core_matches / core_total
                if core_score >= 0.9:  # 90%+ match on core fields
                    # Apply a bonus to the overall score
                    score = max(score, core_score * 0.85)  # Minimum 85% if core fields match well
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _extract_artist_name(self, artist_credit: List[Dict]) -> str:
        """Extract artist name from MusicBrainz artist-credit."""
        if not artist_credit:
            return ''
        
        names = []
        for credit in artist_credit:
            if 'artist' in credit and 'name' in credit['artist']:
                names.append(credit['artist']['name'])
        
        return ', '.join(names)
    
    def _extract_album_name(self, releases: List[Dict]) -> str:
        """Extract album name from MusicBrainz releases."""
        if not releases:
            return ''
        
        # Return the first release title
        return releases[0].get('title', '') if releases else ''
    
    def _extract_release_date(self, releases: List[Dict]) -> str:
        """Extract release date from MusicBrainz releases."""
        if not releases:
            return ''
        
        # Return the first available date
        for release in releases:
            if 'date' in release and release['date']:
                return release['date'][:4]  # Return just the year
        
        return ''
    
    def _merge_metadata(self, current: Dict[str, Any], match: Dict) -> Dict[str, Any]:
        """Merge current metadata with MusicBrainz match data."""
        completed = current.copy()
        
        # Extract metadata from MusicBrainz match
        if 'title' in match and not current.get('title'):
            completed['title'] = match['title']
        
        if 'artist-credit' in match and not current.get('artist'):
            completed['artist'] = self._extract_artist_name(match['artist-credit'])
        
        if 'releases' in match:
            releases = match['releases']
            if releases and not current.get('album'):
                completed['album'] = releases[0].get('title', '')
            
            if releases and not current.get('date'):
                completed['date'] = self._extract_release_date(releases)
        
        # Add MusicBrainz IDs
        if 'id' in match:
            completed['musicbrainz_recording_id'] = match['id']
        
        if 'releases' in match and match['releases']:
            completed['musicbrainz_release_id'] = match['releases'][0].get('id', '')
        
        # Extract genre information if available
        genre_found = False
        
        # Try to get genre from recording level first
        if 'tags' in match and match['tags'] and not current.get('genre'):
            # Use the most common tag as genre
            tags = sorted(match['tags'], key=lambda x: x.get('count', 0), reverse=True)
            if tags:
                completed['genre'] = tags[0]['name']
                genre_found = True
        
        # If no genre found at recording level, check all available releases
        if not genre_found and not current.get('genre') and 'id' in match:
            # Get detailed recording information to access all releases
            recording_details = self.mb_client.get_recording_details(match['id'])
            if recording_details and 'releases' in recording_details:
                # Check all releases until we find one with genre information
                for release in recording_details['releases']:
                    release_id = release.get('id')
                    if release_id:
                        release_details = self.mb_client.get_release_details(release_id)
                        if release_details:
                            # Try genres first (more specific)
                            if 'genres' in release_details and release_details['genres']:
                                genres = sorted(release_details['genres'], key=lambda x: x.get('count', 0), reverse=True)
                                if genres:
                                    completed['genre'] = genres[0]['name']
                                    genre_found = True
                                    break
                            
                            # If no genres, try tags
                            if 'tags' in release_details and release_details['tags']:
                                tags = sorted(release_details['tags'], key=lambda x: x.get('count', 0), reverse=True)
                                if tags:
                                    completed['genre'] = tags[0]['name']
                                    genre_found = True
                                    break
        
        return completed
    
    def batch_complete_metadata(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Complete metadata for multiple files.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary mapping file paths to completed metadata
        """
        results = {}
        
        for i, file_path in enumerate(file_paths, 1):
            logger.info(f"Processing {i}/{len(file_paths)}: {os.path.basename(file_path)}")
            
            try:
                completed_metadata = self.complete_metadata(file_path)
                results[file_path] = completed_metadata
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results[file_path] = {'error': str(e)}
        
        return results