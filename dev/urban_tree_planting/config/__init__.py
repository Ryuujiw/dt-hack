"""
Configuration module for urban tree planting analysis
"""

from .settings import *

__all__ = [
    'GOOGLE_MAPS_API_KEY',
    'KL_REGIONAL_SCALE',
    'KL_REGIONAL_NORTH_OFFSET',
    'KL_REGIONAL_EAST_OFFSET',
    'ZOOM_LEVEL',
    'REGION_NAME',
    'BASE_DIR',
    'OUTPUT_DIR',
    'LOCATIONS_FILE',
    'OSM_USE_CACHE',
    'OSM_TIMEOUT',
    'OSM_MAX_QUERY_AREA',
    'BATCH_DELAY',
    'MAX_RETRIES',
]
