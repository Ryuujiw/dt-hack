"""
Geometry transformer for OSM data alignment

Applies scale and offset transformations to align OSM geometries
with satellite imagery. Uses universal configuration validated
across multiple locations in Kuala Lumpur.
"""

import geopandas as gpd
from shapely import affinity
import pandas as pd

from config.settings import (
    KL_REGIONAL_SCALE,
    KL_REGIONAL_NORTH_OFFSET,
    KL_REGIONAL_EAST_OFFSET,
    PEDESTRIAN_PRIORITY_TYPES,
    LOW_TRAFFIC_TYPES,
    MEDIUM_TRAFFIC_TYPES,
    HIGH_TRAFFIC_TYPES,
)
from utils.geo_utils import meters_to_degrees, calculate_image_bounds
from utils.logger import logger


class GeometryTransformer:
    """
    Transforms OSM geometries to align with satellite imagery

    Applies:
    1. Scale transformation around center point
    2. Position offset (translation)

    Uses proven universal configuration for Kuala Lumpur region.
    """

    def __init__(self,
                 scale=KL_REGIONAL_SCALE,
                 north_offset_m=KL_REGIONAL_NORTH_OFFSET,
                 east_offset_m=KL_REGIONAL_EAST_OFFSET):
        """
        Initialize transformer

        Args:
            scale: Scale factor (default: 1.95 for KL)
            north_offset_m: North offset in meters (default: -5.0)
            east_offset_m: East offset in meters (default: -10.0)
        """
        self.scale = scale
        self.north_offset_m = north_offset_m
        self.east_offset_m = east_offset_m

        logger.debug(f"GeometryTransformer initialized: scale={scale:.2f}x, "
                    f"offset=({north_offset_m:+.2f}m N, {east_offset_m:+.2f}m E)")

    def align(self, gdf, center_lat, center_lon):
        """
        Apply alignment transformation to geometries

        Args:
            gdf: GeoDataFrame to transform
            center_lat: Center latitude
            center_lon: Center longitude

        Returns:
            GeoDataFrame: Transformed geometries
        """
        if len(gdf) == 0:
            return gdf.copy()

        # Convert offset from meters to degrees
        lat_offset, lon_offset = meters_to_degrees(
            self.north_offset_m,
            self.east_offset_m,
            center_lat
        )

        gdf_copy = gdf.copy()

        # Step 1: Scale around center point
        gdf_copy['geometry'] = gdf_copy['geometry'].apply(
            lambda geom: affinity.scale(
                geom,
                xfact=self.scale,
                yfact=self.scale,
                origin=(center_lon, center_lat)
            )
        )

        # Step 2: Apply position offset (translation)
        gdf_copy['geometry'] = gdf_copy['geometry'].apply(
            lambda geom: affinity.translate(
                geom,
                xoff=lon_offset,
                yoff=lat_offset
            )
        )

        logger.debug(f"  Transformed {len(gdf_copy)} geometries")
        return gdf_copy

    def calculate_bounds(self, center_lat, center_lon, image_size):
        """
        Calculate geographic bounds for satellite image

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            image_size: (width, height) tuple in pixels

        Returns:
            tuple: (min_lon, min_lat, max_lon, max_lat)
        """
        img_width, img_height = image_size

        bounds = calculate_image_bounds(
            center_lat,
            center_lon,
            zoom=18,  # Use settings ZOOM_LEVEL if needed
            image_width=img_width // 2,  # Divide by 2 because scale=2 in download
            image_height=img_height // 2,
            scale=2
        )

        logger.debug(f"  Calculated bounds: {bounds}")
        return bounds

    def filter_streets_by_type(self, streets_gdf):
        """
        Filter streets into categories based on highway type

        Categories:
        - pedestrian: Footways, pedestrian streets, paths
        - low_traffic: Residential, tertiary, unclassified
        - medium_traffic: Secondary roads
        - high_traffic: Primary, trunk, motorway

        Args:
            streets_gdf: GeoDataFrame of streets

        Returns:
            dict: Dictionary with keys 'pedestrian', 'low_traffic',
                  'medium_traffic', 'high_traffic'
        """
        if len(streets_gdf) == 0:
            return self._empty_street_dict()

        # Initialize lists
        pedestrian_streets = []
        low_traffic_streets = []
        medium_traffic_streets = []
        high_traffic_streets = []

        # Categorize each street
        for idx, row in streets_gdf.iterrows():
            highway_type = self._get_highway_type(row)

            if highway_type in PEDESTRIAN_PRIORITY_TYPES:
                pedestrian_streets.append(row)
            elif highway_type in LOW_TRAFFIC_TYPES:
                low_traffic_streets.append(row)
            elif highway_type in MEDIUM_TRAFFIC_TYPES:
                medium_traffic_streets.append(row)
            elif highway_type in HIGH_TRAFFIC_TYPES:
                high_traffic_streets.append(row)
            else:
                # Unknown type -> default to low traffic
                low_traffic_streets.append(row)

        result = {
            'pedestrian': self._to_gdf(pedestrian_streets),
            'low_traffic': self._to_gdf(low_traffic_streets),
            'medium_traffic': self._to_gdf(medium_traffic_streets),
            'high_traffic': self._to_gdf(high_traffic_streets),
        }

        logger.debug(f"  Filtered streets: pedestrian={len(result['pedestrian'])}, "
                    f"low={len(result['low_traffic'])}, "
                    f"medium={len(result['medium_traffic'])}, "
                    f"high={len(result['high_traffic'])}")

        return result

    def _get_highway_type(self, row):
        """Extract highway type from row"""
        highway_type = None

        if 'highway' in row:
            highway_type = row['highway']
        elif hasattr(row, 'highway'):
            highway_type = row.highway

        # Handle list types
        if isinstance(highway_type, list):
            highway_type = highway_type[0] if len(highway_type) > 0 else None

        return highway_type

    def _to_gdf(self, rows_list):
        """Convert list of rows to GeoDataFrame"""
        if rows_list:
            return gpd.GeoDataFrame(rows_list, crs='EPSG:4326')
        else:
            return gpd.GeoDataFrame(geometry=[], crs='EPSG:4326')

    def _empty_street_dict(self):
        """Return empty street dictionary"""
        return {
            'pedestrian': gpd.GeoDataFrame(geometry=[], crs='EPSG:4326'),
            'low_traffic': gpd.GeoDataFrame(geometry=[], crs='EPSG:4326'),
            'medium_traffic': gpd.GeoDataFrame(geometry=[], crs='EPSG:4326'),
            'high_traffic': gpd.GeoDataFrame(geometry=[], crs='EPSG:4326'),
        }
