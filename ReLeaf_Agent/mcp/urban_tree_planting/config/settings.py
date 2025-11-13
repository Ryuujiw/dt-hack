"""
Configuration settings for urban tree planting analysis

All constants and configuration values are centralized here.
"""

import os
from pathlib import Path

# ==============================================================================
# API Configuration
# ==============================================================================

# Use environment variable for API key (Cloud Run compatible)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ==============================================================================
# Universal Alignment Configuration (Kuala Lumpur)
# ==============================================================================
# These values were validated across multiple locations in KL
# Scale: 1.95x provides 90%+ accuracy
# Offset: -5m North, -10m East optimally aligns OSM data with satellite imagery

KL_REGIONAL_SCALE = 1.95  # Scale factor for OSM geometries
KL_REGIONAL_NORTH_OFFSET = -5.00  # meters North
KL_REGIONAL_EAST_OFFSET = -10.00  # meters East
ZOOM_LEVEL = 18  # Google Maps zoom level
REGION_NAME = "kuala_lumpur"

# ==============================================================================
# Directory Configuration
# ==============================================================================

BASE_DIR = Path(__file__).parent.parent
# Use /tmp for Cloud Run (ephemeral storage) or fall back to local output
OUTPUT_DIR = Path("/tmp/tree_analysis_output") if os.path.exists("/tmp") else BASE_DIR / "output"
LOCATIONS_FILE = BASE_DIR / "config" / "locations.json"  # Locations file in config/

# ==============================================================================
# OSMnx Configuration
# ==============================================================================

OSM_USE_CACHE = False  # Set to True to enable caching (faster but may have stale data)
OSM_LOG_CONSOLE = False  # Set to True for verbose OSMnx logging
OSM_TIMEOUT = 180  # seconds
OSM_MAX_QUERY_AREA = 50 * 1000 * 50 * 1000  # 50km x 50km

# ==============================================================================
# Processing Configuration
# ==============================================================================

BATCH_DELAY = 10  # seconds between processing locations (rate limiting)
MAX_RETRIES = 3  # maximum retry attempts for downloads

# ==============================================================================
# Image Configuration
# ==============================================================================

SATELLITE_IMAGE_SIZE = "640x640"  # Google Maps image size
SATELLITE_IMAGE_SCALE = 2  # Scale factor (1 or 2)

# ==============================================================================
# Street Classification
# ==============================================================================

PEDESTRIAN_PRIORITY_TYPES = ['footway', 'pedestrian', 'living_street', 'path', 'steps']
LOW_TRAFFIC_TYPES = ['residential', 'tertiary', 'unclassified', 'service']
MEDIUM_TRAFFIC_TYPES = ['secondary', 'secondary_link']
HIGH_TRAFFIC_TYPES = ['primary', 'primary_link', 'trunk', 'trunk_link', 'motorway', 'motorway_link']

# ==============================================================================
# Mask Generation Configuration
# ==============================================================================

STREET_BUFFER_METERS = 10  # Buffer distance for street masks (meters)

# ==============================================================================
# Priority Scoring Configuration
# ==============================================================================

# Priority score weights (total = 100 points)
SCORE_SIDEWALK = 35  # Pedestrian-priority street proximity
SCORE_BUILDING = 25  # Building cooling zones
SCORE_SUN = 20  # Sun exposure gradient
SCORE_AMENITY = 10  # Amenity density (pedestrian traffic proxy)
SCORE_GAP = 10  # Gap filling bonus (reserved for future)

# Building cooling zone distances (meters)
BUILDING_OPTIMAL_MIN = 5
BUILDING_OPTIMAL_MAX = 15
BUILDING_GOOD_MIN = 15
BUILDING_GOOD_MAX = 30
BUILDING_TOO_CLOSE_MAX = 5

# Sidewalk priority distances (pixels)
SIDEWALK_EXCELLENT_MAX = 20  # ≤20px from pedestrian streets
SIDEWALK_GOOD_MIN = 20
SIDEWALK_GOOD_MAX = 50  # 20-50px

# Shadow intensity thresholds (0.0 = no shadow, 1.0 = full shadow)
SHADOW_FULL_SUN_MAX = 0.3  # <30% shadow = full sun
SHADOW_PARTIAL_MIN = 0.3
SHADOW_PARTIAL_MAX = 0.6  # 30-60% shadow = partial shade
SHADOW_HEAVY_MIN = 0.6  # >60% shadow = heavy shade

# Amenity density thresholds (within 50m radius)
AMENITY_SEARCH_RADIUS = 50  # meters
AMENITY_HIGH_THRESHOLD = 10  # ≥10 amenities = high density
AMENITY_MEDIUM_THRESHOLD = 5  # 5-10 amenities = medium density

# Priority level thresholds (0-100 score)
PRIORITY_CRITICAL_MIN = 80  # 80-100 = CRITICAL
PRIORITY_HIGH_MIN = 60  # 60-80 = HIGH
PRIORITY_MEDIUM_MIN = 40  # 40-60 = MEDIUM
# 0-40 = LOW

# ==============================================================================
# Vegetation Detection Configuration
# ==============================================================================

NDVI_THRESHOLD = 0.2  # NDVI > 0.2 indicates vegetation
MIN_VEGETATION_BRIGHTNESS = 60  # Minimum brightness for vegetation (0-255)
SHADOW_BRIGHTNESS_THRESHOLD = 95  # V < 95 = potential shadow
SHADOW_DESATURATION_THRESHOLD = 60  # S < 60 = desaturated (shadow)
SHADOW_VERY_DARK_THRESHOLD = 70  # V < 70 = very dark shadow
SHADOW_MIN_SIZE_PIXELS = 20  # Minimum shadow area to keep (noise removal)

# ==============================================================================
# Visualization Configuration
# ==============================================================================

VISUALIZATION_DPI = 72  # DPI for saved visualizations (reduced for web display)
VISUALIZATION_FIGSIZE = (18, 12)  # Figure size for enhanced analysis (2x3 grid, reduced for chat display)

# Color codes for visualizations (RGB)
COLOR_BUILDING = (128, 128, 128)  # Gray
COLOR_SIDEWALK = (100, 255, 255)  # Cyan
COLOR_SHADOW = (200, 100, 100)  # Light red
COLOR_VEGETATION = (0, 255, 0)  # Green
COLOR_AMENITY = (255, 255, 0)  # Yellow
COLOR_CRITICAL = (255, 0, 0)  # Red
COLOR_HIGH = (255, 165, 0)  # Orange
COLOR_MEDIUM = (255, 255, 0)  # Yellow
COLOR_LOW = (144, 238, 144)  # Light green

# Street colors by traffic level
COLOR_STREET_LOW = (144, 238, 144)  # Light green (low traffic)
COLOR_STREET_MEDIUM = (255, 255, 0)  # Yellow (medium traffic)
COLOR_STREET_HIGH = (255, 165, 0)  # Orange (high traffic)

# ==============================================================================
# Logging Configuration
# ==============================================================================

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
