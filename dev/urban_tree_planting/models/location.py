"""
Location data model

Represents a geographic location and all its processed data
throughout the analysis pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
import geopandas as gpd
from PIL import Image


@dataclass
class Location:
    """
    Represents a location to analyze for tree planting recommendations

    This class holds all data for a location as it progresses through
    the processing pipeline. Initially only name/lat/lon are set,
    and other fields are populated during processing.

    Attributes:
        name: Unique identifier (e.g., "aster_hill")
        description: Human-readable description
        lat: Latitude in decimal degrees (WGS84)
        lon: Longitude in decimal degrees (WGS84)

        # Downloaded data (populated in download step)
        satellite_img: Downloaded satellite image from Google Maps
        buildings_raw: Raw building footprints from OSM
        streets_raw: Raw street network from OSM
        amenities: Amenity points from OSM
        bounds: Geographic bounds (min_lon, min_lat, max_lon, max_lat)

        # Aligned data (populated in transformation step)
        buildings_aligned: Buildings after scale/offset transformation
        streets_aligned: Streets after scale/offset transformation
        streets_by_type: Streets categorized by type (dict)

        # Detection results (populated in detection step)
        vegetation_mask: Boolean array of vegetation pixels
        shadow_mask: Boolean array of shadow pixels
        ndvi: NDVI array (vegetation index)

        # Generated masks (populated in mask generation step)
        building_mask: Boolean array of building pixels
        street_mask: Boolean array of street pixels (with buffer)
        sidewalk_mask: Boolean array of pedestrian-priority street pixels

        # Priority scores (populated in scoring step)
        enhanced_priority_score: Float array of priority scores (0-100)
        critical_priority: Boolean array of CRITICAL priority pixels (80-100)
        high_priority: Boolean array of HIGH priority pixels (60-80)
        medium_priority: Boolean array of MEDIUM priority pixels (40-60)
        low_priority: Boolean array of LOW priority pixels (0-40)
        shadow_intensity: Float array of shadow intensity (0-1)

        # Statistics
        total_pixels: Total image pixels
        vegetation_pixels: Count of vegetation pixels
        shadow_pixels: Count of shadow pixels
        building_pixels: Count of building pixels
        street_pixels: Count of street pixels
        critical_pixels: Count of CRITICAL priority pixels
        high_pixels: Count of HIGH priority pixels
        medium_pixels: Count of MEDIUM priority pixels
        low_pixels: Count of LOW priority pixels

        # Metadata
        scale: Scale factor used
        lat_offset_m: North offset in meters
        lon_offset_m: East offset in meters
        buildings_count: Number of building polygons
        streets_count: Number of street segments
        amenities_count: Number of amenity points
    """

    # Required fields (must be provided at initialization)
    name: str
    description: str
    lat: float
    lon: float

    # Downloaded data (populated during processing)
    satellite_img: Optional[Image.Image] = None
    buildings_raw: Optional[gpd.GeoDataFrame] = None
    streets_raw: Optional[gpd.GeoDataFrame] = None
    amenities: Optional[gpd.GeoDataFrame] = None
    bounds: Optional[tuple] = None  # (min_lon, min_lat, max_lon, max_lat)

    # Aligned data
    buildings_aligned: Optional[gpd.GeoDataFrame] = None
    streets_aligned: Optional[gpd.GeoDataFrame] = None
    streets_by_type: Optional[Dict[str, gpd.GeoDataFrame]] = None

    # Detection results
    vegetation_mask: Optional[np.ndarray] = None
    shadow_mask: Optional[np.ndarray] = None
    ndvi: Optional[np.ndarray] = None

    # Generated masks
    building_mask: Optional[np.ndarray] = None
    street_mask: Optional[np.ndarray] = None
    sidewalk_mask: Optional[np.ndarray] = None

    # Priority scores
    enhanced_priority_score: Optional[np.ndarray] = None
    critical_priority: Optional[np.ndarray] = None
    high_priority: Optional[np.ndarray] = None
    medium_priority: Optional[np.ndarray] = None
    low_priority: Optional[np.ndarray] = None
    shadow_intensity: Optional[np.ndarray] = None

    # Statistics
    total_pixels: int = 0
    vegetation_pixels: int = 0
    shadow_pixels: int = 0
    building_pixels: int = 0
    street_pixels: int = 0
    critical_pixels: int = 0
    high_pixels: int = 0
    medium_pixels: int = 0
    low_pixels: int = 0

    # Metadata
    scale: float = 0.0
    lat_offset_m: float = 0.0
    lon_offset_m: float = 0.0
    buildings_count: int = 0
    streets_count: int = 0
    amenities_count: int = 0

    def __repr__(self):
        return f"Location(name='{self.name}', lat={self.lat:.4f}, lon={self.lon:.4f})"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert location to dictionary (excluding large numpy arrays and images)

        Returns:
            dict: Location data suitable for JSON serialization
        """
        return {
            'name': self.name,
            'description': self.description,
            'lat': self.lat,
            'lon': self.lon,
            'bounds': self.bounds,
            'scale': self.scale,
            'lat_offset_m': self.lat_offset_m,
            'lon_offset_m': self.lon_offset_m,
            'buildings_count': self.buildings_count,
            'streets_count': self.streets_count,
            'amenities_count': self.amenities_count,
            'total_pixels': self.total_pixels,
            'vegetation_pixels': self.vegetation_pixels,
            'shadow_pixels': self.shadow_pixels,
            'building_pixels': self.building_pixels,
            'street_pixels': self.street_pixels,
            'critical_pixels': self.critical_pixels,
            'high_pixels': self.high_pixels,
            'medium_pixels': self.medium_pixels,
            'low_pixels': self.low_pixels,
        }
