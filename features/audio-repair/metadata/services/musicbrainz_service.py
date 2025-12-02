"""
MusicBrainz service for metadata search and retrieval.
"""

import logging
import requests
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode

from ..core.interfaces import MetadataSearchInterface
from ..core.models import AudioMetadata, MetadataSearchResult
from ..core.exceptions import MusicBrainzError

logger = logging.getLogger(__name__)


class MusicBrainzService(MetadataSearchInterface):
    """
    Service for interacting with MusicBrainz API.
    
    Handles rate limiting, error handling, and data transformation
    for MusicBrainz metadata searches.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize MusicBrainz service.
        
        Args:
            config: Configuration dictionary with MusicBrainz settings
        """
        if config is None:
            config = self._get_default_config()
            
        self.base_url = config['base_url']
        self.user_agent = config['user_agent']
        self.rate_limit = config['rate_limit']
        self.timeout = config['timeout']
        self.search_threshold = config.get('search_threshold', 0.8)
        self.max_search_results = config.get('max_search_results', 10)
        
        self.last_request_time = 0
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json'
        })
    
    def search_metadata(self, query_metadata: AudioMetadata, 
                       max_results: int = 10) -> List[MetadataSearchResult]:
        """
        Search for metadata matches using MusicBrainz.
        
        Args:
            query_metadata: Metadata to use for searching
            max_results: Maximum number of results to return
            
        Returns:
            List of MetadataSearchResult objects sorted by confidence
        """
        try:
            # Build search query
            search_params = self._build_search_params(query_metadata)
            if not search_params:
                logger.warning("No searchable parameters found in metadata")
                return []
            
            logger.info(f"Searching with params: {search_params}")
            
            # Search recordings
            response = self._make_request("recording", search_params)
            if not response:
                return []
            
            recordings = response.get('recordings', [])
            logger.info(f"Found {len(recordings)} potential matches")
            
            if not recordings:
                # Fallback: search with just title
                if query_metadata.title:
                    logger.info("Searching with title only")
                    fallback_params = {'query': f'recording:"{query_metadata.title}"'}
                    response = self._make_request("recording", fallback_params)
                    if response:
                        recordings = response.get('recordings', [])
            
            # Convert to search results
            results = []
            for recording in recordings[:max_results]:
                search_result = self._recording_to_search_result(recording, query_metadata)
                if search_result and search_result.confidence_score >= self.search_threshold:
                    results.append(search_result)
            
            # Sort by confidence score
            results.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching MusicBrainz: {e}")
            raise MusicBrainzError(f"Search failed: {e}")
    
    def get_detailed_metadata(self, recording_id: str) -> Optional[AudioMetadata]:
        """
        Get detailed metadata for a specific recording.
        
        Args:
            recording_id: MusicBrainz recording ID
            
        Returns:
            Detailed AudioMetadata or None if not found
        """
        try:
            # Get recording details with releases
            params = {'inc': 'releases+release-groups+artists+genres'}
            response = self._make_request(f"recording/{recording_id}", params)
            
            if not response:
                return None
                
            return self._recording_to_metadata(response)
            
        except Exception as e:
            logger.error(f"Error getting detailed metadata for {recording_id}: {e}")
            return None
    
    def _build_search_params(self, metadata: AudioMetadata) -> Dict[str, str]:
        """Build search parameters from metadata."""
        params = {}
        
        # Build query components
        query_parts = []
        
        if metadata.title:
            query_parts.append(f'recording:"{metadata.title}"')
            
        if metadata.artist:
            query_parts.append(f'artist:"{metadata.artist}"')
            
        if metadata.album:
            query_parts.append(f'release:"{metadata.album}"')
        
        if query_parts:
            params['query'] = ' AND '.join(query_parts)
            params['limit'] = str(self.max_search_results)
            
        return params
    
    def _recording_to_search_result(self, recording: Dict[str, Any], 
                                  query_metadata: AudioMetadata) -> Optional[MetadataSearchResult]:
        """Convert MusicBrainz recording to search result."""
        try:
            metadata = self._recording_to_metadata(recording)
            if not metadata:
                return None
                
            # Calculate confidence score
            confidence = self._calculate_similarity(query_metadata, metadata)
            
            return MetadataSearchResult(
                metadata=metadata,
                confidence_score=confidence,
                source="musicbrainz",
                match_details={
                    'recording_id': recording.get('id'),
                    'score_details': self._get_score_details(query_metadata, metadata)
                }
            )
            
        except Exception as e:
            logger.error(f"Error converting recording to search result: {e}")
            return None
    
    def _recording_to_metadata(self, recording: Dict[str, Any]) -> Optional[AudioMetadata]:
        """Convert MusicBrainz recording data to AudioMetadata."""
        try:
            metadata = AudioMetadata()
            
            # Basic information
            metadata.title = recording.get('title')
            metadata.musicbrainz_recording_id = recording.get('id')
            
            # Artist information
            if 'artist-credit' in recording and recording['artist-credit']:
                artists = [ac.get('name', '') for ac in recording['artist-credit'] 
                          if isinstance(ac, dict)]
                metadata.artist = ', '.join(filter(None, artists))
            
            # Release information (get from first release)
            releases = recording.get('releases', [])
            if releases:
                release = releases[0]
                metadata.album = release.get('title')
                metadata.date = release.get('date')
                metadata.musicbrainz_release_id = release.get('id')
                
                # Try to get genre from release
                if 'release-group' in release:
                    rg = release['release-group']
                    if 'genres' in rg and rg['genres']:
                        metadata.genre = rg['genres'][0].get('name')
            
            metadata.source = "musicbrainz"
            return metadata
            
        except Exception as e:
            logger.error(f"Error converting recording to metadata: {e}")
            return None
    
    def _calculate_similarity(self, query: AudioMetadata, candidate: AudioMetadata) -> float:
        """Calculate similarity score between two metadata objects."""
        from difflib import SequenceMatcher
        
        score = 0.0
        total_weight = 0.0
        
        # Define field weights
        weights = {
            'title': 2.0,
            'artist': 1.5,
            'album': 1.0
        }
        
        for field, weight in weights.items():
            query_value = getattr(query, field, None)
            candidate_value = getattr(candidate, field, None)
            
            if query_value and candidate_value:
                similarity = SequenceMatcher(None, 
                                           query_value.lower(),
                                           candidate_value.lower()).ratio()
                score += similarity * weight
                total_weight += weight
            elif query_value or candidate_value:
                # Penalty for missing field
                total_weight += weight * 0.5
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _get_score_details(self, query: AudioMetadata, candidate: AudioMetadata) -> Dict[str, float]:
        """Get detailed scoring breakdown."""
        from difflib import SequenceMatcher
        
        details = {}
        fields = ['title', 'artist', 'album']
        
        for field in fields:
            query_value = getattr(query, field, None)
            candidate_value = getattr(candidate, field, None)
            
            if query_value and candidate_value:
                similarity = SequenceMatcher(None,
                                           query_value.lower(),
                                           candidate_value.lower()).ratio()
                details[f"{field}_similarity"] = similarity
            else:
                details[f"{field}_similarity"] = 0.0
                
        return details
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make rate-limited request to MusicBrainz API."""
        self._rate_limit_wait()
        
        url = f"{self.base_url}{endpoint}"
        params['fmt'] = 'json'
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MusicBrainz API request failed: {e}")
            if hasattr(e.response, 'status_code'):
                raise MusicBrainzError(f"API request failed: {e}", e.response.status_code)
            else:
                raise MusicBrainzError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in MusicBrainz request: {e}")
            raise MusicBrainzError(f"Unexpected error: {e}")
    
    def _rate_limit_wait(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
            
        self.last_request_time = time.time()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'base_url': 'https://musicbrainz.org/ws/2/',
            'user_agent': 'AudiophileNAS/1.0 (https://github.com/danshani/AudiophileNAS)',
            'rate_limit': 1.0,
            'timeout': 10,
            'search_threshold': 0.8,
            'max_search_results': 10
        }