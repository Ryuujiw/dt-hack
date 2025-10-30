"""
Project Configuration for Menara LGB Urban Tree Planning
=========================================================

This file contains the core configuration parameters for the urban tree planning project.
All team members should import and use these values to ensure consistency.

Usage:
    from config import MENARA_LGB_COORDS, STUDY_RADIUS
"""

# ============================================================================
# LOCATION SETTINGS
# ============================================================================

# Menara LGB (Lembaga Getah Malaysia Building) - EXACT COORDINATES
# Location: Jalan Ampang, Kuala Lumpur, Malaysia
MENARA_LGB_COORDS = (3.13792463037415, 101.62946855487311)
MENARA_LGB_LAT = 3.13792463037415
MENARA_LGB_LON = 101.62946855487311

# Study area radius from the building (in meters)
STUDY_RADIUS = 500  # 500m radius

# Alternative study radii for different use cases
STUDY_RADIUS_SMALL = 250   # 250m for detailed analysis
STUDY_RADIUS_MEDIUM = 500  # 500m for main project (default)
STUDY_RADIUS_LARGE = 1000  # 1km for broader context

# ============================================================================
# NETWORK SETTINGS
# ============================================================================

# Network types for OSMnx queries
NETWORK_TYPE_WALK = 'walk'           # Pedestrian networks
NETWORK_TYPE_DRIVE = 'drive'         # Drivable streets
NETWORK_TYPE_DRIVE_SERVICE = 'drive_service'  # Drivable + service roads
NETWORK_TYPE_ALL = 'all'             # All street types

# Default network type for the project
DEFAULT_NETWORK_TYPE = NETWORK_TYPE_WALK

# ============================================================================
# DATA PATHS
# ============================================================================

from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
SRC_DIR = PROJECT_ROOT / "src"

# Data subdirectories
DATA_3D_CONTEXT = DATA_DIR / "3d_context"
DATA_NETWORKS = DATA_DIR / "networks"
DATA_WEATHER = DATA_DIR / "weather"
DATA_TREES = DATA_DIR / "trees"

# Output file paths
BUILDINGS_FILE = DATA_3D_CONTEXT / "buildings_with_heights.gpkg"
PLANTING_ZONES_FILE = DATA_3D_CONTEXT / "planting_zones.gpkg"
STREET_NETWORK_FILE = DATA_3D_CONTEXT / "street_network.graphml"

# ============================================================================
# BUILDING & ELEVATION SETTINGS
# ============================================================================

# Building height estimation (meters per floor)
METERS_PER_FLOOR = 3.5

# Default building heights by type (meters)
DEFAULT_HEIGHT_COMMERCIAL = 20.0
DEFAULT_HEIGHT_RESIDENTIAL = 15.0
DEFAULT_HEIGHT_UNKNOWN = 10.0

# Tall building threshold (for shade analysis)
TALL_BUILDING_THRESHOLD = 30.0  # meters

# ============================================================================
# TREE PLANTING PRIORITY SETTINGS
# ============================================================================

# Distance thresholds (in METERS - use with projected CRS like UTM)
# NOTE: Always project geometries to UTM (EPSG:32648) before calculating distances!
DISTANCE_FAR_FROM_BUILDING = 50.0   # 50 meters - needs shade trees
DISTANCE_NEAR_BUILDING = 30.0       # 30 meters - check for existing shade
DISTANCE_VERY_CLOSE = 10.0          # 10 meters - too close to building

# Elevation thresholds (meters)
FLOOD_PRONE_ELEVATION = 45.0  # Below this = high flood risk

# ============================================================================
# WEATHER SETTINGS (for Tool 3)
# ============================================================================

# Temperature thresholds (Celsius)
TEMP_HOT_THRESHOLD = 32.0      # Above this = need shade trees
TEMP_WARM_THRESHOLD = 28.0

# Rainfall thresholds (mm per month)
RAINFALL_HIGH_THRESHOLD = 200.0  # Monsoon season
RAINFALL_MODERATE_THRESHOLD = 100.0

# Humidity thresholds (percentage)
HUMIDITY_HIGH_THRESHOLD = 80.0

# Seasons
SEASON_MONSOON = 'monsoon'
SEASON_DRY = 'dry'

# ============================================================================
# MALAYSIAN TREE SPECIES DATABASE
# ============================================================================

MALAYSIAN_TREE_SPECIES = {
    'Rain Tree': {
        'scientific_name': 'Samanea saman',
        'water_absorption': 'high',      # 500L/day
        'shade_coverage': 'excellent',
        'flood_tolerance': 'high',
        'best_planting_season': SEASON_MONSOON,
        'mature_height_m': 25,
        'canopy_spread_m': 30,
        'air_quality_improvement': 'high',
        'notes': 'Excellent for flood mitigation and shade'
    },
    'Angsana': {
        'scientific_name': 'Pterocarpus indicus',
        'water_absorption': 'medium',
        'shade_coverage': 'excellent',
        'flood_tolerance': 'medium',
        'best_planting_season': SEASON_MONSOON,
        'mature_height_m': 30,
        'canopy_spread_m': 20,
        'air_quality_improvement': 'high',
        'notes': 'Dense canopy, beautiful flowering tree'
    },
    'Yellow Flame': {
        'scientific_name': 'Peltophorum pterocarpum',
        'water_absorption': 'medium',
        'shade_coverage': 'good',
        'flood_tolerance': 'medium',
        'best_planting_season': SEASON_MONSOON,
        'mature_height_m': 15,
        'canopy_spread_m': 12,
        'air_quality_improvement': 'medium',
        'notes': 'Good for medium-sized areas, yellow flowers'
    },
    'Sea Apple': {
        'scientific_name': 'Syzygium grande',
        'water_absorption': 'high',
        'shade_coverage': 'good',
        'flood_tolerance': 'high',
        'best_planting_season': SEASON_MONSOON,
        'mature_height_m': 20,
        'canopy_spread_m': 15,
        'air_quality_improvement': 'medium',
        'notes': 'Native species, good for wet areas'
    },
    'Tembusu': {
        'scientific_name': 'Fagraea fragrans',
        'water_absorption': 'medium',
        'shade_coverage': 'good',
        'flood_tolerance': 'low',
        'best_planting_season': SEASON_DRY,
        'mature_height_m': 25,
        'canopy_spread_m': 10,
        'air_quality_improvement': 'medium',
        'notes': 'Drought tolerant, fragrant flowers'
    }
}

# ============================================================================
# OSMNX SETTINGS
# ============================================================================

# Cache and logging
USE_CACHE = True
LOG_CONSOLE = False

# Coordinate reference system
CRS_WGS84 = 'EPSG:4326'  # Standard lat/lon
CRS_UTM = 'EPSG:32648'   # UTM Zone 48N (for KL area)

# ============================================================================
# API KEYS (for production use)
# ============================================================================

# Google Maps Elevation API
# TODO: Add your API key here for production
GOOGLE_ELEVATION_API_KEY = None  # Set this in production

# Weather API (if using)
# TODO: Add weather API key
WEATHER_API_KEY = None  # Set this in production

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_location_dict():
    """Returns location as dictionary"""
    return {
        'lat': MENARA_LGB_LAT,
        'lon': MENARA_LGB_LON,
        'coords': MENARA_LGB_COORDS,
        'name': 'Menara LGB',
        'radius_m': STUDY_RADIUS
    }

def ensure_data_directories():
    """Create data directories if they don't exist"""
    for directory in [DATA_DIR, DATA_3D_CONTEXT, DATA_NETWORKS, DATA_WEATHER, DATA_TREES]:
        directory.mkdir(parents=True, exist_ok=True)

def project_to_utm(gdf):
    """
    Project a GeoDataFrame from WGS84 (lat/lon) to UTM Zone 48N (meters).

    Use this before calculating distances to ensure accuracy!

    Args:
        gdf: GeoDataFrame in any CRS

    Returns:
        GeoDataFrame projected to EPSG:32648 (UTM Zone 48N for KL area)

    Example:
        >>> buildings_utm = project_to_utm(buildings)
        >>> distance_m = buildings_utm.geometry.distance(point_utm).min()
    """
    return gdf.to_crs(CRS_UTM)

def create_point_utm(lat, lon):
    """
    Create a point geometry in UTM coordinates.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        Shapely Point in UTM coordinates (EPSG:32648)

    Example:
        >>> point = create_point_utm(3.1379, 101.6295)
        >>> distance = buildings_utm.geometry.distance(point).min()
    """
    import geopandas as gpd
    from shapely.geometry import Point

    point_wgs84 = Point(lon, lat)
    point_gdf = gpd.GeoDataFrame({'geometry': [point_wgs84]}, crs=CRS_WGS84)
    point_utm = point_gdf.to_crs(CRS_UTM).geometry.iloc[0]
    return point_utm

if __name__ == "__main__":
    # Test configuration
    print("Menara LGB Urban Tree Planning - Configuration")
    print("=" * 60)
    print(f"Location: {MENARA_LGB_COORDS}")
    print(f"Study Radius: {STUDY_RADIUS}m")
    print(f"Data Directory: {DATA_DIR}")
    print(f"\nAvailable Tree Species: {len(MALAYSIAN_TREE_SPECIES)}")
    for species, info in MALAYSIAN_TREE_SPECIES.items():
        print(f"  - {species} ({info['scientific_name']})")
    print("=" * 60)
