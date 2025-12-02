"""
Configuration settings for metadata operations.
"""

import os
from typing import Dict, Any

# MusicBrainz API Configuration
MUSICBRAINZ_CONFIG = {
    'base_url': 'https://musicbrainz.org/ws/2/',
    'user_agent': 'AudiophileNAS/1.0 (https://github.com/danshani/AudiophileNAS)',
    'rate_limit': 1.0,  # Requests per second
    'timeout': 10,  # Request timeout in seconds
}

# Metadata completion settings
METADATA_CONFIG = {
    'required_fields': [
        'title',
        'artist', 
        'album',
        'date',
        'genre',
        'track_number'
    ],
    'optional_fields': [
        'album_artist',
        'composer',
        'performer',
        'conductor',
        'label',
        'catalog_number',
        'disc_number',
        'total_tracks',
        'total_discs',
        'isrc',
        'musicbrainz_track_id',
        'musicbrainz_recording_id',
        'musicbrainz_release_id',
        'musicbrainz_artist_id'
    ],
    'search_threshold': 0.8,  # Minimum similarity score for matches
    'max_search_results': 10,
    'fuzzy_matching': True
}

# File format specific metadata mappings
FORMAT_METADATA_MAPPING = {
    'flac': {
        'title': 'TITLE',
        'artist': 'ARTIST',
        'album': 'ALBUM',
        'date': 'DATE',
        'genre': 'GENRE',
        'track_number': 'TRACKNUMBER',
        'album_artist': 'ALBUMARTIST',
        'composer': 'COMPOSER'
    },
    'mp3': {
        'title': 'TIT2',
        'artist': 'TPE1',
        'album': 'TALB',
        'date': 'TDRC',
        'genre': 'TCON',
        'track_number': 'TRCK',
        'album_artist': 'TPE2',
        'composer': 'TCOM'
    },
    'mp4': {
        'title': '\xa9nam',
        'artist': '\xa9ART',
        'album': '\xa9alb',
        'date': '\xa9day',
        'genre': '\xa9gen',
        'track_number': 'trkn',
        'album_artist': 'aART',
        'composer': '\xa9wrt'
    }
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary."""
    return {
        'musicbrainz': MUSICBRAINZ_CONFIG,
        'metadata': METADATA_CONFIG,
        'format_mapping': FORMAT_METADATA_MAPPING
    }