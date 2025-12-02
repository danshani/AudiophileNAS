"""
MusicBrainz API client for metadata retrieval.
"""

import requests
import time
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import logging

from .config import MUSICBRAINZ_CONFIG

logger = logging.getLogger(__name__)

class MusicBrainzClient:
    """Client for interacting with MusicBrainz API."""
    
    def __init__(self):
        self.base_url = MUSICBRAINZ_CONFIG['base_url']
        self.user_agent = MUSICBRAINZ_CONFIG['user_agent']
        self.rate_limit = MUSICBRAINZ_CONFIG['rate_limit']
        self.timeout = MUSICBRAINZ_CONFIG['timeout']
        self.last_request_time = 0
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json'
        })
    
    def _rate_limit_wait(self):
        """Ensure rate limiting compliance."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make a request to MusicBrainz API with rate limiting."""
        self._rate_limit_wait()
        
        url = f"{self.base_url}{endpoint}"
        params['fmt'] = 'json'
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"MusicBrainz API request failed: {e}")
            return None
    
    def search_recordings(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for recordings using query string.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of recording dictionaries
        """
        params = {
            'query': query,
            'limit': limit
        }
        
        result = self._make_request('recording', params)
        if result and 'recordings' in result:
            return result['recordings']
        return []
    
    def search_by_metadata(self, title: str, artist: str = None, album: str = None, 
                          limit: int = 10) -> List[Dict]:
        """
        Search for recordings by metadata fields.
        
        Args:
            title: Track title
            artist: Artist name
            album: Album name
            limit: Maximum number of results
            
        Returns:
            List of recording dictionaries
        """
        query_parts = [f'recording:"{title}"']
        
        if artist:
            query_parts.append(f'artist:"{artist}"')
        if album:
            query_parts.append(f'release:"{album}"')
        
        query = ' AND '.join(query_parts)
        return self.search_recordings(query, limit)
    
    def get_recording_details(self, recording_id: str) -> Optional[Dict]:
        """
        Get detailed information about a recording.
        
        Args:
            recording_id: MusicBrainz recording ID
            
        Returns:
            Recording details dictionary
        """
        params = {
            'inc': 'releases+artist-credits+genres+tags+ratings'
        }
        
        return self._make_request(f'recording/{recording_id}', params)
    
    def get_release_details(self, release_id: str) -> Optional[Dict]:
        """
        Get detailed information about a release.
        
        Args:
            release_id: MusicBrainz release ID
            
        Returns:
            Release details dictionary
        """
        params = {
            'inc': 'artist-credits+genres+tags+labels+recordings+media'
        }
        
        return self._make_request(f'release/{release_id}', params)
    
    def search_releases(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for releases using query string.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of release dictionaries
        """
        params = {
            'query': query,
            'limit': limit
        }
        
        result = self._make_request('release', params)
        if result and 'releases' in result:
            return result['releases']
        return []
    
    def get_artist_details(self, artist_id: str) -> Optional[Dict]:
        """
        Get detailed information about an artist.
        
        Args:
            artist_id: MusicBrainz artist ID
            
        Returns:
            Artist details dictionary
        """
        params = {
            'inc': 'genres+tags+ratings+aliases'
        }
        
        return self._make_request(f'artist/{artist_id}', params)