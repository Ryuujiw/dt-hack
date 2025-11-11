"""
Mask generator for converting geometries to pixel masks

Converts vector geometries (buildings, streets) to raster pixel masks
for analysis and priority calculation.
"""

import numpy as np
from PIL import Image, ImageDraw

from config.settings import STREET_BUFFER_METERS
from utils.geo_utils import latlon_to_pixel
from utils.logger import logger


class MaskGenerator:
    """
    Generates pixel masks from vector geometries

    Converts:
    - Building polygons -> Building mask
    - Street linestrings -> Street mask (with buffer)
    - Pedestrian streets -> Sidewalk mask
    """

    def __init__(self):
        """Initialize mask generator"""
        logger.debug("MaskGenerator initialized")

    def create_mask(self, geometries_gdf, satellite_img, bounds):
        """
        Create binary mask from geometries

        Args:
            geometries_gdf: GeoDataFrame of geometries (buildings or streets)
            satellite_img: PIL Image
            bounds: (min_lon, min_lat, max_lon, max_lat) tuple

        Returns:
            tuple: (mask, count)
                - mask: Boolean numpy array
                - count: Number of geometries drawn
        """
        if len(geometries_gdf) == 0:
            img_width, img_height = satellite_img.size
            return np.zeros((img_height, img_width), dtype=bool), 0

        img_width, img_height = satellite_img.size
        min_lon, min_lat, max_lon, max_lat = bounds

        # Create mask image (black background)
        mask = Image.new('L', (img_width, img_height), 0)
        draw = ImageDraw.Draw(mask)

        # Draw each geometry
        count = 0
        for idx, row in geometries_gdf.iterrows():
            geom = row.geometry

            # Handle different geometry types
            if geom.geom_type == 'MultiPolygon':
                polygons = list(geom.geoms)
            elif geom.geom_type == 'Polygon':
                polygons = [geom]
            elif geom.geom_type == 'LineString':
                # For streets, buffer to create polygon
                polygons = [geom.buffer(0.00005)]  # Small buffer in degrees
            else:
                continue

            for poly in polygons:
                if poly.geom_type != 'Polygon':
                    continue

                # Convert exterior coordinates to pixels
                exterior_coords = list(poly.exterior.coords)
                pixel_coords = [
                    latlon_to_pixel(
                        lat, lon,
                        min_lat, max_lat, min_lon, max_lon,
                        img_height, img_width
                    )
                    for lon, lat in exterior_coords
                ]

                # Draw filled polygon in white
                if len(pixel_coords) >= 3:
                    draw.polygon(pixel_coords, fill=255)
                    count += 1

        # Convert to boolean array
        mask_array = np.array(mask) > 0

        logger.debug(f"  Created mask: {count} geometries, {np.sum(mask_array)} pixels")
        return mask_array, count

    def create_street_mask(self, streets_gdf, satellite_img, bounds,
                          buffer_m=STREET_BUFFER_METERS):
        """
        Create street mask with buffer

        Projects to UTM for accurate buffering, then creates mask.

        Args:
            streets_gdf: GeoDataFrame of streets
            satellite_img: PIL Image
            bounds: (min_lon, min_lat, max_lon, max_lat) tuple
            buffer_m: Buffer distance in meters

        Returns:
            tuple: (mask, count)
        """
        if len(streets_gdf) == 0:
            img_width, img_height = satellite_img.size
            return np.zeros((img_height, img_width), dtype=bool), 0

        logger.debug(f"  Creating street mask with {buffer_m}m buffer...")

        # Project to UTM for accurate buffering
        # UTM Zone 48N for Kuala Lumpur
        streets_utm = streets_gdf.to_crs('EPSG:32648')

        # Apply buffer
        streets_buffered = streets_utm.copy()
        streets_buffered.geometry = streets_buffered.buffer(buffer_m)

        # Project back to WGS84
        streets_buffered = streets_buffered.to_crs('EPSG:4326')

        # Create mask
        mask, count = self.create_mask(streets_buffered, satellite_img, bounds)

        logger.debug(f"  Street mask created: {count} buffered streets")
        return mask, count

    def create_sidewalk_mask(self, pedestrian_streets, low_traffic_streets,
                            satellite_img, bounds, buffer_m=5):
        """
        Create sidewalk mask for pedestrian-priority streets

        Combines pedestrian and low-traffic streets as sidewalk candidates.

        Args:
            pedestrian_streets: GeoDataFrame of pedestrian streets
            low_traffic_streets: GeoDataFrame of low traffic streets
            satellite_img: PIL Image
            bounds: (min_lon, min_lat, max_lon, max_lat) tuple
            buffer_m: Buffer distance in meters (default: 5m)

        Returns:
            Boolean array: Sidewalk mask
        """
        import pandas as pd
        import geopandas as gpd

        # Combine pedestrian + low traffic streets
        if len(pedestrian_streets) > 0 or len(low_traffic_streets) > 0:
            sidewalk_streets = gpd.GeoDataFrame(
                pd.concat([pedestrian_streets, low_traffic_streets], ignore_index=True),
                crs='EPSG:4326'
            )
        else:
            sidewalk_streets = gpd.GeoDataFrame(geometry=[], crs='EPSG:4326')

        if len(sidewalk_streets) == 0:
            img_width, img_height = satellite_img.size
            return np.zeros((img_height, img_width), dtype=bool)

        # Create mask with buffer
        logger.debug(f"  Creating sidewalk mask from {len(sidewalk_streets)} streets...")

        # Project to UTM
        sidewalk_utm = sidewalk_streets.to_crs('EPSG:32648')

        # Buffer
        sidewalk_buffered = sidewalk_utm.copy()
        sidewalk_buffered.geometry = sidewalk_buffered.buffer(buffer_m)

        # Project back
        sidewalk_buffered = sidewalk_buffered.to_crs('EPSG:4326')

        # Create mask
        mask, count = self.create_mask(sidewalk_buffered, satellite_img, bounds)

        logger.debug(f"  Sidewalk mask created: {count} buffered sidewalks")
        return mask

    def create_comprehensive_street_mask(self, pedestrian_streets, low_traffic_streets,
                                        medium_traffic_streets, high_traffic_streets,
                                        satellite_img, bounds):
        """
        Create comprehensive street exclusion mask with tiered buffers

        Uses different buffer sizes based on traffic level:
        - High-traffic (motorway, primary, trunk): 25m buffer
        - Medium-traffic (secondary): 15m buffer
        - Low-traffic (residential, tertiary): 10m buffer
        - Pedestrian (footway, paths): 5m buffer

        Args:
            pedestrian_streets: GeoDataFrame of pedestrian streets
            low_traffic_streets: GeoDataFrame of low traffic streets
            medium_traffic_streets: GeoDataFrame of medium traffic streets
            high_traffic_streets: GeoDataFrame of high traffic streets
            satellite_img: PIL Image
            bounds: (min_lon, min_lat, max_lon, max_lat) tuple

        Returns:
            Boolean array: Comprehensive street exclusion mask
        """
        img_width, img_height = satellite_img.size
        comprehensive_mask = np.zeros((img_height, img_width), dtype=bool)

        # High-traffic streets: 25m buffer (motorways, primary roads)
        if len(high_traffic_streets) > 0:
            logger.debug(f"  Creating high-traffic mask from {len(high_traffic_streets)} streets (25m buffer)...")
            high_mask, _ = self.create_street_mask(
                high_traffic_streets, satellite_img, bounds, buffer_m=25
            )
            comprehensive_mask = comprehensive_mask | high_mask

        # Medium-traffic streets: 15m buffer (secondary roads)
        if len(medium_traffic_streets) > 0:
            logger.debug(f"  Creating medium-traffic mask from {len(medium_traffic_streets)} streets (15m buffer)...")
            medium_mask, _ = self.create_street_mask(
                medium_traffic_streets, satellite_img, bounds, buffer_m=15
            )
            comprehensive_mask = comprehensive_mask | medium_mask

        # Low-traffic streets: 10m buffer
        if len(low_traffic_streets) > 0:
            logger.debug(f"  Creating low-traffic mask from {len(low_traffic_streets)} streets (10m buffer)...")
            low_mask, _ = self.create_street_mask(
                low_traffic_streets, satellite_img, bounds, buffer_m=10
            )
            comprehensive_mask = comprehensive_mask | low_mask

        # Pedestrian streets: 5m buffer
        if len(pedestrian_streets) > 0:
            logger.debug(f"  Creating pedestrian mask from {len(pedestrian_streets)} streets (5m buffer)...")
            ped_mask, _ = self.create_street_mask(
                pedestrian_streets, satellite_img, bounds, buffer_m=5
            )
            comprehensive_mask = comprehensive_mask | ped_mask

        total_pixels = np.sum(comprehensive_mask)
        logger.debug(f"  Comprehensive street mask created: {total_pixels} pixels excluded")

        return comprehensive_mask
