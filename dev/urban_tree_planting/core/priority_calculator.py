"""
Priority calculator for tree planting recommendations

Calculates enhanced 100-point priority scores based on:
1. Sidewalk proximity (35 points)
2. Building cooling zones (25 points)
3. Sun exposure (20 points)
4. Amenity density (10 points)
5. Gap filling bonus (10 points - reserved)
"""

import numpy as np
from scipy.ndimage import distance_transform_edt
import geopandas as gpd
from shapely.geometry import Point

from config.settings import (
    SCORE_SIDEWALK,
    SCORE_BUILDING,
    SCORE_SUN,
    SCORE_AMENITY,
    SCORE_GAP,
    PRIORITY_CRITICAL_MIN,
    PRIORITY_HIGH_MIN,
    PRIORITY_MEDIUM_MIN,
)
from utils.geo_utils import latlon_to_pixel
from utils.logger import logger


class PriorityCalculator:
    """
    Calculates priority scores for tree planting locations

    Uses multiple factors:
    - Proximity to pedestrian areas (sidewalks)
    - Distance from buildings (cooling effect zones)
    - Sun exposure intensity (from shadow analysis)
    - Amenity density (pedestrian traffic proxy)
    - Gap filling bonus (future use)
    """

    def __init__(self):
        """Initialize priority calculator"""
        logger.debug("PriorityCalculator initialized")

    def calculate(self, location, shadow_intensity, sidewalk_mask,
                  building_mask, street_mask, vegetation_mask, amenities_gdf, bounds):
        """
        Calculate enhanced priority scores

        Args:
            location: Location object
            shadow_intensity: Float array (0-1) of shadow intensity
            sidewalk_mask: Boolean array of sidewalk areas
            building_mask: Boolean array of building footprints
            street_mask: Boolean array of street areas
            vegetation_mask: Boolean array of existing vegetation
            amenities_gdf: GeoDataFrame of amenity points
            bounds: (min_lon, min_lat, max_lon, max_lat) tuple

        Returns:
            dict: {
                'enhanced_priority_score': Float array (0-100),
                'critical_priority': Boolean array (80-100),
                'high_priority': Boolean array (60-80),
                'medium_priority': Boolean array (40-60),
                'low_priority': Boolean array (0-40),
                'sidewalk_component': Float array (0-35),
                'building_component': Float array (0-25),
                'sun_component': Float array (0-20),
                'amenity_component': Float array (0-10),
            }
        """
        logger.debug("Calculating enhanced priority scores...")

        img_height, img_width = shadow_intensity.shape

        # Component 1: Sidewalk proximity (35 points)
        sidewalk_score = self._calculate_sidewalk_priority(
            sidewalk_mask, max_points=SCORE_SIDEWALK
        )

        # Component 2: Building cooling zones (25 points)
        building_score = self._calculate_building_priority(
            building_mask, max_points=SCORE_BUILDING
        )

        # Component 3: Sun exposure (20 points)
        sun_score = self._calculate_sun_priority(
            shadow_intensity, max_points=SCORE_SUN
        )

        # Component 4: Amenity density (10 points)
        amenity_score = self._calculate_amenity_priority(
            amenities_gdf, bounds, (img_width, img_height), max_points=SCORE_AMENITY
        )

        # Component 5: Gap filling bonus (10 points - reserved for future)
        gap_score = np.zeros((img_height, img_width), dtype=np.float32)

        # Combine all components
        enhanced_priority = (
            sidewalk_score +
            building_score +
            sun_score +
            amenity_score +
            gap_score
        )

        # Valid area: Exclude buildings, streets, and existing vegetation
        # This makes results more focused than just excluding buildings+vegetation
        valid_area = (~building_mask) & (~street_mask) & (~vegetation_mask)
        enhanced_priority = enhanced_priority * valid_area

        # Categorize into priority levels
        critical_priority = (enhanced_priority >= PRIORITY_CRITICAL_MIN) & valid_area
        high_priority = (enhanced_priority >= PRIORITY_HIGH_MIN) & (enhanced_priority < PRIORITY_CRITICAL_MIN) & valid_area
        medium_priority = (enhanced_priority >= PRIORITY_MEDIUM_MIN) & (enhanced_priority < PRIORITY_HIGH_MIN) & valid_area
        low_priority = (enhanced_priority > 0) & (enhanced_priority < PRIORITY_MEDIUM_MIN) & valid_area

        # Calculate statistics
        total_valid = np.sum(valid_area)
        if total_valid > 0:
            critical_pct = np.sum(critical_priority) / total_valid * 100
            high_pct = np.sum(high_priority) / total_valid * 100
            medium_pct = np.sum(medium_priority) / total_valid * 100
            low_pct = np.sum(low_priority) / total_valid * 100

            logger.debug(f"  Priority distribution:")
            logger.debug(f"    Critical (80-100): {critical_pct:.1f}%")
            logger.debug(f"    High (60-80): {high_pct:.1f}%")
            logger.debug(f"    Medium (40-60): {medium_pct:.1f}%")
            logger.debug(f"    Low (0-40): {low_pct:.1f}%")

        return {
            'enhanced_priority_score': enhanced_priority,
            'critical_priority': critical_priority,
            'high_priority': high_priority,
            'medium_priority': medium_priority,
            'low_priority': low_priority,
            'sidewalk_component': sidewalk_score,
            'building_component': building_score,
            'sun_component': sun_score,
            'amenity_component': amenity_score,
        }

    def _calculate_sidewalk_priority(self, sidewalk_mask, max_points=35):
        """
        Calculate sidewalk proximity priority (PIXEL-BASED like notebook)

        Scoring (in PIXELS):
        - ≤20 pixels: 35 points (excellent - very close to pedestrian areas)
        - 20-50 pixels: 20 points (good proximity)
        - >50 pixels: 5 points (low priority - far from pedestrian areas)

        Args:
            sidewalk_mask: Boolean array
            max_points: Maximum points (default: 35)

        Returns:
            Float array: Sidewalk priority scores
        """
        if not np.any(sidewalk_mask):
            return np.zeros_like(sidewalk_mask, dtype=np.float32)

        # Calculate distance transform (in pixels)
        distance_px = distance_transform_edt(~sidewalk_mask)

        # Apply pixel-based scoring (matching notebook exactly)
        score = np.zeros_like(distance_px, dtype=np.float32)
        score[distance_px <= 20] = 35  # Excellent
        score[(distance_px > 20) & (distance_px <= 50)] = 20  # Good
        score[distance_px > 50] = 5  # Low priority

        return score

    def _calculate_building_priority(self, building_mask, max_points=25):
        """
        Calculate building cooling zone priority (matching notebook)

        Optimal planting zones near buildings for shade/cooling:
        - 5-15m: 25 points (optimal cooling zone)
        - 15-30m: 15 points (good cooling zone)
        - 0-5m: 10 points (too close, but still some benefit)
        - >30m: 5 points (minimal benefit)

        Args:
            building_mask: Boolean array
            max_points: Maximum points (default: 25)

        Returns:
            Float array: Building priority scores
        """
        if not np.any(building_mask):
            return np.zeros_like(building_mask, dtype=np.float32)

        # Calculate distance from buildings (in pixels)
        distance_px = distance_transform_edt(~building_mask)

        # Convert to meters using 0.6m per pixel (matching notebook)
        meters_per_pixel = 0.6
        distance_m = distance_px * meters_per_pixel

        # Apply distance-based scoring (matching notebook exactly)
        score = np.zeros_like(distance_m, dtype=np.float32)
        score[(distance_m >= 5) & (distance_m <= 15)] = 25  # Optimal
        score[(distance_m > 15) & (distance_m <= 30)] = 15  # Good
        score[(distance_m > 0) & (distance_m < 5)] = 10  # Too close
        score[distance_m > 30] = 5  # Minimal benefit

        return score

    def _calculate_sun_priority(self, shadow_intensity, max_points=20):
        """
        Calculate sun exposure priority (matching notebook)

        Areas with high sun exposure benefit more from shade trees:
        - Full sun (shadow_intensity < 0.3): 20 points - needs shade trees
        - Partial sun (0.3-0.6): 12 points - still good for planting
        - Heavy shade (≥0.6): 5 points - low priority

        Args:
            shadow_intensity: Float array (0-1, where 1=full shadow)
            max_points: Maximum points (default: 20)

        Returns:
            Float array: Sun exposure scores
        """
        score = np.zeros_like(shadow_intensity, dtype=np.float32)

        # Apply scoring (matching notebook exactly)
        score[shadow_intensity < 0.3] = 20  # Full sun
        score[(shadow_intensity >= 0.3) & (shadow_intensity < 0.6)] = 12  # Partial
        score[shadow_intensity >= 0.6] = 5  # Heavy shade

        return score

    def _calculate_amenity_priority(self, amenities_gdf, bounds,
                                    image_size, max_points=10, sample_radius_m=50):
        """
        Calculate amenity density priority

        Higher density of amenities = more pedestrian traffic = higher priority.
        Uses spatial sampling with circular kernel.

        Args:
            amenities_gdf: GeoDataFrame of amenity points
            bounds: (min_lon, min_lat, max_lon, max_lat)
            image_size: (width, height) in pixels
            max_points: Maximum points (default: 10)
            sample_radius_m: Sampling radius in meters (default: 50m)

        Returns:
            Float array: Amenity density scores
        """
        img_width, img_height = image_size
        min_lon, min_lat, max_lon, max_lat = bounds

        if len(amenities_gdf) == 0:
            return np.zeros((img_height, img_width), dtype=np.float32)

        # Create amenity density map
        density_map = np.zeros((img_height, img_width), dtype=np.float32)

        # Convert amenities to pixel coordinates
        amenity_pixels = []
        for idx, row in amenities_gdf.iterrows():
            point = row.geometry
            if point.geom_type == 'Point':
                px_x, px_y = latlon_to_pixel(
                    point.y, point.x,
                    min_lat, max_lat, min_lon, max_lon,
                    img_height, img_width
                )
                amenity_pixels.append((px_x, px_y))

        if len(amenity_pixels) == 0:
            return density_map

        # Convert radius from meters to pixels
        meters_per_pixel = 0.3
        radius_px = int(sample_radius_m / meters_per_pixel)

        # Create circular kernel
        kernel_size = radius_px * 2 + 1
        kernel = np.zeros((kernel_size, kernel_size), dtype=np.float32)
        center = radius_px
        for i in range(kernel_size):
            for j in range(kernel_size):
                dist = np.sqrt((i - center)**2 + (j - center)**2)
                if dist <= radius_px:
                    # Gaussian-like falloff
                    kernel[i, j] = np.exp(-(dist / radius_px)**2)

        # Apply kernel around each amenity
        for px_x, px_y in amenity_pixels:
            # Bounds for kernel application
            y_start = max(0, px_y - radius_px)
            y_end = min(img_height, px_y + radius_px + 1)
            x_start = max(0, px_x - radius_px)
            x_end = min(img_width, px_x + radius_px + 1)

            # Kernel bounds (handle edge cases)
            ky_start = radius_px - (px_y - y_start)
            ky_end = radius_px + (y_end - px_y)
            kx_start = radius_px - (px_x - x_start)
            kx_end = radius_px + (x_end - px_x)

            # Add kernel to density map
            density_map[y_start:y_end, x_start:x_end] += kernel[ky_start:ky_end, kx_start:kx_end]

        # Normalize to 0-1
        if density_map.max() > 0:
            density_map = density_map / density_map.max()

        # Scale to max_points
        score = density_map * max_points

        return score
