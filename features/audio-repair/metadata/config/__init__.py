"""
Configuration module for metadata processing.
"""

from .settings import (
    MUSICBRAINZ_CONFIG, 
    METADATA_CONFIG, 
    FORMAT_METADATA_MAPPING,
    get_config
)

__all__ = ['MUSICBRAINZ_CONFIG', 'METADATA_CONFIG', 'FORMAT_METADATA_MAPPING', 'get_config']