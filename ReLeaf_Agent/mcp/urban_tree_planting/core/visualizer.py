"""
Result visualizer for tree planting analysis

Generates comprehensive 6-panel visualizations showing:
1. Original satellite image
2. Detected vegetation (NDVI)
3. Shadow detection
4. Street/building alignment
5. Priority scores
6. Final recommendations
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import ListedColormap
from PIL import Image
import os

from ..config.settings import (
    COLOR_CRITICAL,
    COLOR_HIGH,
    COLOR_MEDIUM,
    COLOR_LOW,
    COLOR_VEGETATION,
    COLOR_SHADOW,
    COLOR_BUILDING,
    COLOR_SIDEWALK,
    COLOR_STREET_LOW,
    COLOR_STREET_MEDIUM,
    COLOR_STREET_HIGH,
    VISUALIZATION_DPI,
    VISUALIZATION_FIGSIZE,
)
from ..utils.logger import logger


class ResultVisualizer:
    """
    Generates visualization outputs for tree planting analysis

    Creates multi-panel figures showing:
    - Original imagery
    - Detection results (vegetation, shadows)
    - Alignment overlays (buildings, streets)
    - Priority scoring
    - Final recommendations
    """

    def __init__(self):
        """Initialize visualizer"""
        logger.debug("ResultVisualizer initialized")

    def create_enhanced_visualization(self, location, priority_results, output_path):
        """
        Create 6-panel enhanced analysis visualization

        Panels:
        1. Original satellite image
        2. Vegetation detection (NDVI overlay)
        3. Shadow detection
        4. OSM alignment (buildings + streets)
        5. Priority score heatmap
        6. Final recommendations (color-coded by priority)

        Args:
            location: Location object with all data
            priority_results: Dictionary from PriorityCalculator
            output_path: Path to save PNG file

        Returns:
            str: Path to saved visualization
        """
        logger.debug(f"Creating enhanced visualization for {location.name}...")

        # Extract data
        satellite_img = location.satellite_img
        vegetation_mask = location.vegetation_mask
        shadow_mask = location.shadow_mask
        ndvi = location.ndvi

        buildings_aligned = location.buildings_aligned
        streets_aligned = location.streets_aligned
        pedestrian_streets = location.pedestrian_streets
        low_traffic_streets = location.low_traffic_streets
        medium_traffic_streets = location.medium_traffic_streets
        high_traffic_streets = location.high_traffic_streets

        building_mask = location.building_mask
        sidewalk_mask = location.sidewalk_mask

        enhanced_priority = priority_results['enhanced_priority_score']
        critical_priority = priority_results['critical_priority']
        high_priority = priority_results['high_priority']
        medium_priority = priority_results['medium_priority']
        low_priority = priority_results['low_priority']

        # Create figure
        fig, axes = plt.subplots(2, 3, figsize=VISUALIZATION_FIGSIZE)
        fig.suptitle(f'Enhanced Tree Planting Analysis: {location.name}', fontsize=16, fontweight='bold')

        # Panel 1: Original satellite image
        ax1 = axes[0, 0]
        ax1.imshow(satellite_img)
        ax1.set_title('1. Original Satellite Image')
        ax1.axis('off')

        # Panel 2: Vegetation detection (NDVI)
        ax2 = axes[0, 1]
        ax2.imshow(satellite_img)
        if vegetation_mask is not None:
            veg_overlay = np.zeros((*vegetation_mask.shape, 4))
            veg_overlay[vegetation_mask] = COLOR_VEGETATION + (0.6,)  # Green with alpha
            ax2.imshow(veg_overlay)
        ax2.set_title('2. Vegetation Detection (NDVI)')
        ax2.axis('off')

        # Panel 3: Shadow detection
        ax3 = axes[0, 2]
        ax3.imshow(satellite_img)
        if shadow_mask is not None:
            shadow_overlay = np.zeros((*shadow_mask.shape, 4))
            shadow_overlay[shadow_mask] = COLOR_SHADOW + (0.5,)  # Blue with alpha
            ax3.imshow(shadow_overlay)
        ax3.set_title('3. Shadow Detection')
        ax3.axis('off')

        # Panel 4: OSM alignment (buildings + streets)
        ax4 = axes[1, 0]
        ax4.imshow(satellite_img)

        # Overlay buildings (red)
        if building_mask is not None:
            building_overlay = np.zeros((*building_mask.shape, 4))
            building_overlay[building_mask] = COLOR_BUILDING + (0.4,)
            ax4.imshow(building_overlay)

        # Overlay sidewalks (yellow)
        if sidewalk_mask is not None:
            sidewalk_overlay = np.zeros((*sidewalk_mask.shape, 4))
            sidewalk_overlay[sidewalk_mask] = COLOR_SIDEWALK + (0.5,)
            ax4.imshow(sidewalk_overlay)

        # Overlay streets (color by traffic level)
        bounds = location.bounds
        if bounds is not None:
            self._plot_streets(ax4, low_traffic_streets, bounds, satellite_img.size,
                             COLOR_STREET_LOW, 'Low traffic', linewidth=1.5)
            self._plot_streets(ax4, medium_traffic_streets, bounds, satellite_img.size,
                             COLOR_STREET_MEDIUM, 'Medium traffic', linewidth=2)
            self._plot_streets(ax4, high_traffic_streets, bounds, satellite_img.size,
                             COLOR_STREET_HIGH, 'High traffic', linewidth=2.5)

        ax4.set_title('4. OSM Alignment (Buildings + Streets)')
        ax4.axis('off')

        # Panel 5: Priority score heatmap
        ax5 = axes[1, 1]
        im = ax5.imshow(enhanced_priority, cmap='YlOrRd', vmin=0, vmax=100)
        ax5.set_title('5. Priority Score Heatmap (0-100)')
        ax5.axis('off')
        plt.colorbar(im, ax=ax5, fraction=0.046, pad=0.04)

        # Panel 6: Final recommendations (OVERLAID ON SATELLITE IMAGE)
        ax6 = axes[1, 2]

        # Start with satellite image as base
        ax6.imshow(satellite_img)

        # Create transparent overlays for each priority level
        # Low priority (lightest, most transparent)
        if np.any(low_priority):
            low_overlay = np.zeros((*low_priority.shape, 4))
            low_overlay[low_priority] = [c/255 for c in COLOR_LOW] + [0.5]  # 50% opacity
            ax6.imshow(low_overlay)

        # Medium priority
        if np.any(medium_priority):
            medium_overlay = np.zeros((*medium_priority.shape, 4))
            medium_overlay[medium_priority] = [c/255 for c in COLOR_MEDIUM] + [0.6]  # 60% opacity
            ax6.imshow(medium_overlay)

        # High priority
        if np.any(high_priority):
            high_overlay = np.zeros((*high_priority.shape, 4))
            high_overlay[high_priority] = [c/255 for c in COLOR_HIGH] + [0.7]  # 70% opacity
            ax6.imshow(high_overlay)

        # Critical priority (most opaque for highest visibility)
        if np.any(critical_priority):
            critical_overlay = np.zeros((*critical_priority.shape, 4))
            critical_overlay[critical_priority] = [c/255 for c in COLOR_CRITICAL] + [0.8]  # 80% opacity
            ax6.imshow(critical_overlay)

        ax6.set_title('6. Planting Recommendations\n(Overlaid on Satellite Image)')
        ax6.axis('off')

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=[c/255 for c in COLOR_CRITICAL], label='Critical (80-100)', alpha=0.8),
            Patch(facecolor=[c/255 for c in COLOR_HIGH], label='High (60-80)', alpha=0.7),
            Patch(facecolor=[c/255 for c in COLOR_MEDIUM], label='Medium (40-60)', alpha=0.6),
            Patch(facecolor=[c/255 for c in COLOR_LOW], label='Low (0-40)', alpha=0.5),
        ]
        ax6.legend(handles=legend_elements, loc='upper right', fontsize=8)

        # Adjust layout
        plt.tight_layout()

        # Save figure
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=VISUALIZATION_DPI, bbox_inches='tight')
        plt.close()

        # Compress the image to reduce file size for web display
        try:
            img = Image.open(output_path)
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            # Resize to max width of 1200px while maintaining aspect ratio
            max_width = 1200
            if img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            # Save with optimization and quality reduction
            img.save(output_path, 'PNG', optimize=True, quality=85)
            logger.debug(f"  ✓ Image compressed and optimized: {output_path}")
        except Exception as e:
            logger.warning(f"  ⚠ Could not compress image: {e}")

        logger.debug(f"  ✓ Visualization saved: {output_path}")
        return output_path

    def create_component_breakdown(self, location, priority_results, output_path):
        """
        Create detailed component breakdown visualization

        Shows individual scoring components:
        1. Sidewalk proximity (35 pts)
        2. Building cooling zones (25 pts)
        3. Sun exposure (20 pts)
        4. Amenity density (10 pts)

        Args:
            location: Location object
            priority_results: Dictionary from PriorityCalculator
            output_path: Path to save PNG file

        Returns:
            str: Path to saved visualization
        """
        logger.debug(f"Creating component breakdown for {location.name}...")

        satellite_img = location.satellite_img
        sidewalk_component = priority_results['sidewalk_component']
        building_component = priority_results['building_component']
        sun_component = priority_results['sun_component']
        amenity_component = priority_results['amenity_component']

        # Create figure
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f'Priority Score Components: {location.name}', fontsize=14, fontweight='bold')

        # Component 1: Sidewalk proximity (35 pts)
        ax1 = axes[0, 0]
        im1 = ax1.imshow(sidewalk_component, cmap='Greens', vmin=0, vmax=35)
        ax1.set_title('Sidewalk Proximity (max: 35 pts)')
        ax1.axis('off')
        plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)

        # Component 2: Building cooling zones (25 pts)
        ax2 = axes[0, 1]
        im2 = ax2.imshow(building_component, cmap='Blues', vmin=0, vmax=25)
        ax2.set_title('Building Cooling Zones (max: 25 pts)')
        ax2.axis('off')
        plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

        # Component 3: Sun exposure (20 pts)
        ax3 = axes[1, 0]
        im3 = ax3.imshow(sun_component, cmap='Oranges', vmin=0, vmax=20)
        ax3.set_title('Sun Exposure (max: 20 pts)')
        ax3.axis('off')
        plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)

        # Component 4: Amenity density (10 pts)
        ax4 = axes[1, 1]
        im4 = ax4.imshow(amenity_component, cmap='Purples', vmin=0, vmax=10)
        ax4.set_title('Amenity Density (max: 10 pts)')
        ax4.axis('off')
        plt.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)

        # Adjust layout
        plt.tight_layout()

        # Save figure
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=VISUALIZATION_DPI, bbox_inches='tight')
        plt.close()

        logger.debug(f"  ✓ Component breakdown saved: {output_path}")
        return output_path

    def _plot_streets(self, ax, streets_gdf, bounds, image_size, color, label, linewidth=2):
        """
        Plot street geometries on axis

        Args:
            ax: Matplotlib axis
            streets_gdf: GeoDataFrame of streets
            bounds: (min_lon, min_lat, max_lon, max_lat)
            image_size: (width, height) in pixels
            color: RGB tuple (0-255)
            label: Legend label
            linewidth: Line width
        """
        if len(streets_gdf) == 0:
            return

        from ..utils.geo_utils import latlon_to_pixel

        min_lon, min_lat, max_lon, max_lat = bounds
        img_width, img_height = image_size

        # Convert color to 0-1 range
        color_norm = tuple(c / 255 for c in color)

        # Plot each street
        for idx, row in streets_gdf.iterrows():
            geom = row.geometry

            if geom.geom_type == 'LineString':
                coords = list(geom.coords)
            elif geom.geom_type == 'MultiLineString':
                # Take first linestring
                coords = list(geom.geoms[0].coords) if len(geom.geoms) > 0 else []
            else:
                continue

            if len(coords) < 2:
                continue

            # Convert to pixel coordinates
            pixel_coords = []
            for lon, lat in coords:
                px_x, px_y = latlon_to_pixel(
                    lat, lon,
                    min_lat, max_lat, min_lon, max_lon,
                    img_height, img_width
                )
                pixel_coords.append((px_x, px_y))

            # Plot line
            xs = [p[0] for p in pixel_coords]
            ys = [p[1] for p in pixel_coords]
            ax.plot(xs, ys, color=color_norm, linewidth=linewidth, alpha=0.7)

    def create_summary_statistics(self, location, priority_results):
        """
        Generate summary statistics in JSON format with critical spot coordinates

        Args:
            location: Location object
            priority_results: Dictionary from PriorityCalculator

        Returns:
            dict: Structured summary data
        """
        import cv2
        from ..utils.geo_utils import pixel_to_latlon

        enhanced_priority = priority_results['enhanced_priority_score']
        critical_priority = priority_results['critical_priority']
        high_priority = priority_results['high_priority']
        medium_priority = priority_results['medium_priority']
        low_priority = priority_results['low_priority']

        vegetation_mask = location.vegetation_mask
        building_mask = location.building_mask
        shadow_mask = location.shadow_mask

        img_height, img_width = enhanced_priority.shape
        total_pixels = img_height * img_width

        # Calculate areas
        plantable = ~building_mask & ~vegetation_mask
        total_plantable = np.sum(plantable)

        critical_area = np.sum(critical_priority)
        high_area = np.sum(high_priority)
        medium_area = np.sum(medium_priority)
        low_area = np.sum(low_priority)

        vegetation_area = np.sum(vegetation_mask)
        building_area = np.sum(building_mask)
        shadow_area = np.sum(shadow_mask)

        # Pixel to square meters (0.6m per pixel)
        px_to_m2 = 0.6 * 0.6

        # Extract critical priority spots with coordinates
        critical_spots = self._extract_critical_spots(
            critical_priority, enhanced_priority, location.bounds, img_height, img_width
        )

        # Build structured summary (convert all numpy types to Python native types)
        summary = {
            "location": {
                "name": location.name,
                "description": location.description,
                "center_coordinates": {
                    "latitude": float(location.lat),
                    "longitude": float(location.lon)
                }
            },
            "analysis_metadata": {
                "timestamp": "2025-01-10",
                "total_area_m2": round(float(total_pixels * px_to_m2), 1),
                "image_dimensions": {
                    "width_px": int(img_width),
                    "height_px": int(img_height)
                }
            },
            "land_coverage": {
                "buildings": {
                    "area_m2": round(float(building_area * px_to_m2), 1),
                    "percentage": round(float(building_area)/float(total_pixels)*100, 1),
                    "count": len(location.buildings_aligned) if location.buildings_aligned is not None else 0
                },
                "existing_vegetation": {
                    "area_m2": round(float(vegetation_area * px_to_m2), 1),
                    "percentage": round(float(vegetation_area)/float(total_pixels)*100, 1)
                },
                "shadows": {
                    "area_m2": round(float(shadow_area * px_to_m2), 1),
                    "percentage": round(float(shadow_area)/float(total_pixels)*100, 1)
                },
                "plantable_area": {
                    "area_m2": round(float(total_plantable * px_to_m2), 1),
                    "percentage": round(float(total_plantable)/float(total_pixels)*100, 1)
                }
            },
            "priority_distribution": {
                "critical": {
                    "score_range": "80-100",
                    "area_m2": round(float(critical_area * px_to_m2), 1),
                    "percentage_of_plantable": round(float(critical_area)/float(total_plantable)*100, 1) if total_plantable > 0 else 0.0,
                    "spots_count": len(critical_spots)
                },
                "high": {
                    "score_range": "60-80",
                    "area_m2": round(float(high_area * px_to_m2), 1),
                    "percentage_of_plantable": round(float(high_area)/float(total_plantable)*100, 1) if total_plantable > 0 else 0.0
                },
                "medium": {
                    "score_range": "40-60",
                    "area_m2": round(float(medium_area * px_to_m2), 1),
                    "percentage_of_plantable": round(float(medium_area)/float(total_plantable)*100, 1) if total_plantable > 0 else 0.0
                },
                "low": {
                    "score_range": "0-40",
                    "area_m2": round(float(low_area * px_to_m2), 1),
                    "percentage_of_plantable": round(float(low_area)/float(total_plantable)*100, 1) if total_plantable > 0 else 0.0
                }
            },
            "street_network": {
                "total_streets": len(location.streets_aligned) if location.streets_aligned is not None else 0,
                "pedestrian_streets": len(location.pedestrian_streets) if location.pedestrian_streets is not None else 0,
                "low_traffic_streets": len(location.low_traffic_streets) if location.low_traffic_streets is not None else 0,
                "medium_traffic_streets": len(location.medium_traffic_streets) if location.medium_traffic_streets is not None else 0,
                "high_traffic_streets": len(location.high_traffic_streets) if location.high_traffic_streets is not None else 0
            },
            "amenities": {
                "total_count": len(location.amenities) if location.amenities is not None else 0
            },
            "critical_priority_spots": critical_spots,
            "recommendations": {
                "immediate_action": "Focus on critical priority spots (80-100 score) for immediate tree planting",
                "secondary_targets": "High priority areas (60-80) are excellent for phase 2",
                "long_term_planning": "Medium priority areas (40-60) for long-term urban greening",
                "note": "Low priority areas (0-40) have minimal cooling/environmental impact"
            }
        }

        return summary

    def _extract_critical_spots(self, critical_priority, priority_score, bounds, img_height, img_width):
        """
        Extract critical priority clusters and their center coordinates

        Args:
            critical_priority: Boolean array of critical areas
            priority_score: Float array of scores
            bounds: (min_lon, min_lat, max_lon, max_lat)
            img_height: Image height in pixels
            img_width: Image width in pixels

        Returns:
            list: List of critical spot dictionaries with coordinates
        """
        import cv2
        from ..utils.geo_utils import pixel_to_latlon

        if not np.any(critical_priority):
            return []

        # Find connected components (individual critical clusters)
        critical_uint8 = critical_priority.astype(np.uint8)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            critical_uint8, connectivity=8
        )

        min_lon, min_lat, max_lon, max_lat = bounds
        critical_spots = []

        # Process each cluster (skip background label 0)
        for i in range(1, num_labels):
            area_pixels = int(stats[i, cv2.CC_STAT_AREA])

            # Skip very small clusters (< 20 pixels to catch more spots)
            if area_pixels < 20:
                continue

            # Get centroid in pixel coordinates
            centroid_x = float(centroids[i][0])  # Column (x)
            centroid_y = float(centroids[i][1])  # Row (y)

            # Convert pixel coordinates to lat/lon
            lat, lon = pixel_to_latlon(
                centroid_x, centroid_y,
                min_lat, max_lat, min_lon, max_lon,
                img_height, img_width
            )

            # Get average priority score for this cluster
            cluster_mask = (labels == i)
            avg_score = float(np.mean(priority_score[cluster_mask]))

            # Area in square meters (0.6m per pixel)
            area_m2 = float(area_pixels * (0.6 * 0.6))

            spot = {
                "spot_id": int(i),
                "coordinates": {
                    "latitude": round(float(lat), 8),
                    "longitude": round(float(lon), 8)
                },
                "priority_score": round(avg_score, 1),
                "area_m2": round(area_m2, 1),
                "area_pixels": area_pixels,
                "google_street_view_url": f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}",
                "google_maps_url": f"https://www.google.com/maps?q={lat},{lon}"
            }

            critical_spots.append(spot)

        # Sort by priority score (highest first)
        critical_spots.sort(key=lambda x: x['priority_score'], reverse=True)

        return critical_spots
