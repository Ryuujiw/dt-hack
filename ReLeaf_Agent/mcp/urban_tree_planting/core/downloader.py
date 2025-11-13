"""
Data downloader for satellite imagery and OpenStreetMap data

Downloads satellite imagery from Google Maps API and OSM data
(buildings, streets, amenities) with retry logic and rate limiting.
"""

import requests
from PIL import Image
from io import BytesIO
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
import math
import time

from ..config.settings import (
    GOOGLE_MAPS_API_KEY,
    ZOOM_LEVEL,
    SATELLITE_IMAGE_SIZE,
    SATELLITE_IMAGE_SCALE,
    MAX_RETRIES,
)
from ..utils.logger import logger


class DataDownloader:
    """
    Downloads satellite imagery and OSM data

    Handles:
    - Google Maps Static API for satellite imagery
    - OSMnx for building footprints
    - OSMnx for street networks
    - OSMnx for amenity points
    - Retry logic with exponential backoff
    - Rate limiting between requests
    """

    def __init__(self, api_key=GOOGLE_MAPS_API_KEY):
        """
        Initialize downloader

        Args:
            api_key: Google Maps API key
        """
        self.api_key = api_key

    def download_satellite_image(self, lat, lon, zoom=ZOOM_LEVEL,
                                 size=SATELLITE_IMAGE_SIZE,
                                 scale=SATELLITE_IMAGE_SCALE):
        """
        Download satellite image from Google Maps Static API

        Args:
            lat: Latitude
            lon: Longitude
            zoom: Zoom level (default: from settings)
            size: Image size (default: "640x640")
            scale: Scale factor (1 or 2, default: 2)

        Returns:
            PIL.Image: Downloaded satellite image in RGB format

        Raises:
            requests.HTTPError: If download fails
        """
        logger.debug(f"Downloading satellite image for ({lat:.6f}, {lon:.6f})")

        url = "https://maps.googleapis.com/maps/api/staticmap"
        params = {
            "center": f"{lat},{lon}",
            "zoom": zoom,
            "size": size,
            "maptype": "satellite",
            "scale": scale,
            "key": self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))

            # Ensure RGB format
            if img.mode != 'RGB':
                img = img.convert('RGB')

            logger.debug(f"  ✓ Downloaded {img.size[0]}×{img.size[1]} satellite image")
            return img

        except requests.RequestException as e:
            logger.error(f"  ✗ Failed to download satellite image: {e}")
            raise

    def download_osm_data(self, lat, lon, min_lat, max_lat, min_lon, max_lon,
                         max_retries=MAX_RETRIES):
        """
        Download OSM buildings and streets with retry logic

        Args:
            lat, lon: Center coordinates
            min_lat, max_lat, min_lon, max_lon: Bounding box
            max_retries: Number of retry attempts

        Returns:
            tuple: (buildings_gdf, streets_gdf) GeoDataFrames
        """
        logger.debug(f"Downloading OSM data for ({lat:.6f}, {lon:.6f})")

        center_point = (lat, lon)

        # Calculate radius from bounding box
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        lat_meters = lat_range * 111000
        lon_meters = lon_range * 111000 * math.cos(math.radians(lat))
        diagonal_meters = math.sqrt(lat_meters**2 + lon_meters**2)
        radius = diagonal_meters / 2 * 1.1  # Add 10% buffer

        bbox_polygon = box(min_lon, min_lat, max_lon, max_lat)

        # Download buildings
        buildings = self._download_buildings(
            center_point, radius, bbox_polygon, max_retries
        )

        time.sleep(2)  # Rate limiting between buildings and streets

        # Download streets
        streets = self._download_streets(
            center_point, radius, bbox_polygon, max_retries
        )

        logger.debug(f"  ✓ OSM data downloaded: {len(buildings)} buildings, {len(streets)} streets")
        return buildings, streets

    def _download_buildings(self, center_point, radius, bbox_polygon, max_retries):
        """
        Download building footprints with retry logic

        Args:
            center_point: (lat, lon) tuple
            radius: Search radius in meters
            bbox_polygon: Shapely polygon for clipping
            max_retries: Maximum retry attempts

        Returns:
            GeoDataFrame: Building footprints
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"    → Downloading buildings (attempt {attempt+1}/{max_retries})")

                raw_buildings = ox.features_from_point(
                    center_point,
                    tags={'building': True},
                    dist=radius
                )

                # Filter to polygons only
                raw_buildings = raw_buildings[
                    raw_buildings.geometry.type.isin(['Polygon', 'MultiPolygon'])
                ]

                # Clip to bounding box
                buildings_list = []
                for idx, row in raw_buildings.iterrows():
                    try:
                        if row.geometry.is_valid and bbox_polygon.intersects(row.geometry):
                            buildings_list.append(row)
                    except Exception:
                        continue

                buildings = gpd.GeoDataFrame(buildings_list, crs='EPSG:4326')
                logger.debug(f"    ✓ Buildings downloaded: {len(buildings)}")
                return buildings

            except Exception as e:
                logger.warning(f"    ⚠ Buildings download failed: {e}")

                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                    logger.debug(f"    ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"    ✗ Buildings download failed after {max_retries} attempts")
                    return gpd.GeoDataFrame(geometry=[], crs='EPSG:4326')

    def _download_streets(self, center_point, radius, bbox_polygon, max_retries):
        """
        Download street network with retry logic

        Args:
            center_point: (lat, lon) tuple
            radius: Search radius in meters
            bbox_polygon: Shapely polygon for clipping
            max_retries: Maximum retry attempts

        Returns:
            GeoDataFrame: Street network
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"    → Downloading streets (attempt {attempt+1}/{max_retries})")

                graph = ox.graph_from_point(
                    center_point,
                    dist=radius,
                    network_type='all'
                )

                raw_streets = ox.graph_to_gdfs(graph, nodes=False, edges=True)

                # Clip to bounding box
                streets_list = []
                for idx, row in raw_streets.iterrows():
                    try:
                        if row.geometry.is_valid and bbox_polygon.intersects(row.geometry):
                            streets_list.append(row)
                    except Exception:
                        continue

                streets = gpd.GeoDataFrame(streets_list, crs='EPSG:4326')
                logger.debug(f"    ✓ Streets downloaded: {len(streets)}")
                return streets

            except Exception as e:
                logger.warning(f"    ⚠ Streets download failed: {e}")

                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Exponential backoff
                    logger.debug(f"    ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"    ✗ Streets download failed after {max_retries} attempts")
                    return gpd.GeoDataFrame(geometry=[], crs='EPSG:4326')

    def download_amenities(self, lat, lon, min_lat, max_lat, min_lon, max_lon):
        """
        Download amenity points from OSM

        Downloads restaurants, shops, transit, schools, hospitals, etc.
        Used as proxy for pedestrian traffic density.

        Args:
            lat, lon: Center coordinates
            min_lat, max_lat, min_lon, max_lon: Bounding box

        Returns:
            GeoDataFrame: Amenity points
        """
        center_point = (lat, lon)

        # Calculate radius
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        lat_meters = lat_range * 111000
        lon_meters = lon_range * 111000 * math.cos(math.radians(lat))
        diagonal_meters = math.sqrt(lat_meters**2 + lon_meters**2)
        radius = diagonal_meters / 2 * 1.1

        bbox_polygon = box(min_lon, min_lat, max_lon, max_lat)

        # Amenity tags to download
        amenity_tags = {
            'amenity': [
                'restaurant', 'cafe', 'fast_food', 'bar', 'pub',
                'school', 'university', 'college', 'library',
                'hospital', 'clinic', 'pharmacy',
                'bank', 'post_office', 'police', 'fire_station',
                'bus_station', 'theatre', 'cinema', 'community_centre'
            ],
            'shop': True,  # All shops
            'public_transport': ['station', 'stop_position', 'platform']
        }

        all_amenities = []

        # Download each amenity type
        for tag_key, tag_values in amenity_tags.items():
            try:
                if tag_values is True:
                    # Get all values for this tag
                    features = ox.features_from_point(
                        center_point,
                        tags={tag_key: True},
                        dist=radius
                    )
                else:
                    # Get specific values
                    features = ox.features_from_point(
                        center_point,
                        tags={tag_key: tag_values},
                        dist=radius
                    )

                # Filter to points within bounds
                if len(features) > 0:
                    for idx, row in features.iterrows():
                        try:
                            geom = row.geometry

                            # Convert to point if needed
                            if geom.geom_type == 'Point':
                                point = geom
                            elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                                point = geom.centroid
                            else:
                                continue

                            if bbox_polygon.contains(point):
                                all_amenities.append({
                                    'geometry': point,
                                    'type': tag_key
                                })
                        except Exception:
                            continue

            except Exception:
                # Some amenity types may not exist in the area
                continue

        if len(all_amenities) > 0:
            amenities_gdf = gpd.GeoDataFrame(all_amenities, crs='EPSG:4326')
        else:
            amenities_gdf = gpd.GeoDataFrame(geometry=[], crs='EPSG:4326')

        logger.debug(f"  ✓ Amenities downloaded: {len(amenities_gdf)}")
        return amenities_gdf
