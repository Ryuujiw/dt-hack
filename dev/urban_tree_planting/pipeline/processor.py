"""
Main processing pipeline for urban tree planting analysis

Orchestrates the complete workflow from data download to visualization.
"""

from typing import List, Optional
import time
from pathlib import Path

from models.location import Location
from core.downloader import DataDownloader
from core.transformer import GeometryTransformer
from core.detector import VegetationDetector
from core.mask_generator import MaskGenerator
from core.priority_calculator import PriorityCalculator
from core.visualizer import ResultVisualizer
from utils.logger import logger
from config.settings import BATCH_DELAY, OUTPUT_DIR


class TreePlantingPipeline:
    """
    Main pipeline for urban tree planting analysis

    Processing workflow:
    1. Download data (satellite imagery + OSM buildings/streets/amenities)
    2. Align geometries (apply universal KL transformation)
    3. Detect features (vegetation via NDVI, shadows via brightness)
    4. Generate masks (building mask, sidewalk mask, street mask)
    5. Calculate priority (enhanced 100-point scoring system)
    6. Visualize results (6-panel analysis + component breakdown)
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize pipeline with all core modules

        Args:
            output_dir: Directory for saving results (default: from settings)
        """
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize all core modules
        self.downloader = DataDownloader()
        self.transformer = GeometryTransformer()
        self.detector = VegetationDetector()
        self.mask_generator = MaskGenerator()
        self.priority_calculator = PriorityCalculator()
        self.visualizer = ResultVisualizer()

        logger.debug("TreePlantingPipeline initialized")
        logger.debug(f"  Output directory: {self.output_dir}")

    def process_location(self, location: Location) -> Location:
        """
        Process a single location through the entire pipeline

        Args:
            location: Location object with name, lat, lon, description

        Returns:
            Location: Updated location with all processed data and results

        Raises:
            Exception: If any processing step fails
        """
        logger.info("=" * 70)
        logger.info(f"PROCESSING: {location.name}")
        logger.info(f"Description: {location.description}")
        logger.info(f"Coordinates: ({location.lat:.6f}, {location.lon:.6f})")
        logger.info("=" * 70)

        try:
            # Step 1: Download data
            logger.info("\n[STEP 1/6] Downloading data...")
            location = self._download_data(location)

            # Step 2: Align geometries
            logger.info("\n[STEP 2/6] Aligning geometries...")
            location = self._align_geometries(location)

            # Step 3: Detect features
            logger.info("\n[STEP 3/6] Detecting vegetation and shadows...")
            location = self._detect_features(location)

            # Step 4: Generate masks
            logger.info("\n[STEP 4/6] Generating masks...")
            location = self._generate_masks(location)

            # Step 5: Calculate priority
            logger.info("\n[STEP 5/6] Calculating priority scores...")
            location = self._calculate_priority(location)

            # Step 6: Visualize
            logger.info("\n[STEP 6/6] Generating visualizations...")
            location = self._visualize(location)

            logger.info("\n" + "=" * 70)
            logger.info(f"✅ {location.name} processing COMPLETE!")
            logger.info("=" * 70 + "\n")

            return location

        except Exception as e:
            logger.error(f"\n{'='*70}")
            logger.error(f"✗ FAILED to process {location.name}")
            logger.error(f"Error: {e}")
            logger.error("=" * 70 + "\n")
            raise

    def process_batch(self, locations: List[Location],
                     delay_between: Optional[int] = None) -> List[Location]:
        """
        Process multiple locations with rate limiting

        Args:
            locations: List of Location objects
            delay_between: Seconds to wait between locations (default: from settings)

        Returns:
            List[Location]: List of successfully processed locations
        """
        delay = delay_between if delay_between is not None else BATCH_DELAY

        logger.info("\n" + "=" * 70)
        logger.info("BATCH PROCESSING START")
        logger.info(f"Total locations: {len(locations)}")
        logger.info(f"Delay between locations: {delay}s")
        logger.info("=" * 70 + "\n")

        results = []
        failed = []

        for i, location in enumerate(locations, 1):
            logger.info(f"\n📍 Location {i}/{len(locations)}: {location.name}")

            try:
                result = self.process_location(location)
                results.append(result)

                # Rate limiting (except after last location)
                if i < len(locations):
                    logger.info(f"⏳ Waiting {delay}s before next location...\n")
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"❌ Skipping {location.name} due to error: {e}\n")
                failed.append((location.name, str(e)))
                continue

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("BATCH PROCESSING COMPLETE")
        logger.info(f"✅ Successful: {len(results)}/{len(locations)}")
        if failed:
            logger.info(f"❌ Failed: {len(failed)}")
            for name, error in failed:
                logger.info(f"   - {name}: {error}")
        logger.info("=" * 70 + "\n")

        return results

    def _download_data(self, location: Location) -> Location:
        """
        Step 1: Download satellite imagery and OSM data

        Downloads:
        - Satellite image from Google Maps Static API
        - Building footprints from OSM
        - Street network from OSM
        - Amenity points from OSM
        """
        # Download satellite image
        location.satellite_img = self.downloader.download_satellite_image(
            location.lat, location.lon
        )

        # Calculate geographic bounds
        location.bounds = self.transformer.calculate_bounds(
            location.lat, location.lon, location.satellite_img.size
        )
        min_lon, min_lat, max_lon, max_lat = location.bounds
        logger.debug(f"  Bounds: ({min_lat:.6f}, {min_lon:.6f}) to ({max_lat:.6f}, {max_lon:.6f})")

        # Download OSM data
        location.buildings_raw, location.streets_raw = self.downloader.download_osm_data(
            location.lat, location.lon,
            min_lat, max_lat, min_lon, max_lon
        )

        # Download amenities (for priority scoring)
        location.amenities = self.downloader.download_amenities(
            location.lat, location.lon,
            min_lat, max_lat, min_lon, max_lon
        )

        return location

    def _align_geometries(self, location: Location) -> Location:
        """
        Step 2: Apply alignment transformation to OSM geometries

        Applies universal KL regional transformation:
        - Scale: 1.95x around center point
        - Offset: -5m North, -10m East
        """
        # Align buildings
        location.buildings_aligned = self.transformer.align(
            location.buildings_raw,
            location.lat,
            location.lon
        )

        # Align streets
        location.streets_aligned = self.transformer.align(
            location.streets_raw,
            location.lat,
            location.lon
        )

        # Filter streets by traffic type
        street_categories = self.transformer.filter_streets_by_type(
            location.streets_aligned
        )

        location.pedestrian_streets = street_categories['pedestrian']
        location.low_traffic_streets = street_categories['low_traffic']
        location.medium_traffic_streets = street_categories['medium_traffic']
        location.high_traffic_streets = street_categories['high_traffic']

        return location

    def _detect_features(self, location: Location) -> Location:
        """
        Step 3: Detect vegetation and shadows

        Detection methods:
        - Vegetation: NDVI (Green - Red) / (Green + Red) > threshold
        - Shadows: Low brightness + low saturation, excluding vegetation
        """
        shadow_mask, vegetation_mask, ndvi = self.detector.detect(
            location.satellite_img
        )

        location.shadow_mask = shadow_mask
        location.vegetation_mask = vegetation_mask
        location.ndvi = ndvi

        # Calculate shadow intensity for priority scoring
        location.shadow_intensity = self.detector.calculate_shadow_intensity(
            location.satellite_img
        )

        return location

    def _generate_masks(self, location: Location) -> Location:
        """
        Step 4: Generate pixel masks from vector geometries

        Creates masks for:
        - Buildings (footprints)
        - Streets (tiered buffers: 25m for motorways, 15m for secondary, 10m for local, 5m for pedestrian)
        - Sidewalks (pedestrian + low traffic streets, buffered by 5m)
        """
        # Building mask
        building_mask, building_count = self.mask_generator.create_mask(
            location.buildings_aligned,
            location.satellite_img,
            location.bounds
        )
        location.building_mask = building_mask

        # Comprehensive street mask with tiered buffers (NEW!)
        # High-traffic: 25m, Medium: 15m, Low: 10m, Pedestrian: 5m
        street_mask = self.mask_generator.create_comprehensive_street_mask(
            location.pedestrian_streets,
            location.low_traffic_streets,
            location.medium_traffic_streets,
            location.high_traffic_streets,
            location.satellite_img,
            location.bounds
        )
        location.street_mask = street_mask

        # Sidewalk mask (pedestrian + low traffic, 5m buffer)
        sidewalk_mask = self.mask_generator.create_sidewalk_mask(
            location.pedestrian_streets,
            location.low_traffic_streets,
            location.satellite_img,
            location.bounds,
            buffer_m=5
        )
        location.sidewalk_mask = sidewalk_mask

        logger.debug(f"  Masks created: {building_count} buildings")

        return location

    def _calculate_priority(self, location: Location) -> Location:
        """
        Step 5: Calculate enhanced priority scores

        100-point scoring system:
        - Sidewalk proximity: 35 points
        - Building cooling zones: 25 points
        - Sun exposure: 20 points
        - Amenity density: 10 points
        - Gap filling bonus: 10 points (reserved)
        """
        priority_results = self.priority_calculator.calculate(
            location,
            location.shadow_intensity,
            location.sidewalk_mask,
            location.building_mask,
            location.street_mask,
            location.vegetation_mask,
            location.amenities,
            location.bounds
        )

        # Store all priority data
        location.enhanced_priority_score = priority_results['enhanced_priority_score']
        location.critical_priority = priority_results['critical_priority']
        location.high_priority = priority_results['high_priority']
        location.medium_priority = priority_results['medium_priority']
        location.low_priority = priority_results['low_priority']

        # Store component scores for detailed analysis
        location.sidewalk_component = priority_results['sidewalk_component']
        location.building_component = priority_results['building_component']
        location.sun_component = priority_results['sun_component']
        location.amenity_component = priority_results['amenity_component']

        return location

    def _visualize(self, location: Location) -> Location:
        """
        Step 6: Generate visualizations

        Creates:
        1. Enhanced 6-panel analysis visualization
        2. Component breakdown (4 scoring components)
        3. Summary statistics text file
        """
        # Create location-specific output directory
        location_dir = self.output_dir / location.name.lower().replace(' ', '_')
        location_dir.mkdir(parents=True, exist_ok=True)

        # Priority results for visualizer
        priority_results = {
            'enhanced_priority_score': location.enhanced_priority_score,
            'critical_priority': location.critical_priority,
            'high_priority': location.high_priority,
            'medium_priority': location.medium_priority,
            'low_priority': location.low_priority,
            'sidewalk_component': location.sidewalk_component,
            'building_component': location.building_component,
            'sun_component': location.sun_component,
            'amenity_component': location.amenity_component,
        }

        # 1. Enhanced 6-panel visualization
        enhanced_viz_path = location_dir / f"{location.name.lower().replace(' ', '_')}_analysis.png"
        self.visualizer.create_enhanced_visualization(
            location,
            priority_results,
            enhanced_viz_path
        )

        # 2. Component breakdown
        component_viz_path = location_dir / f"{location.name.lower().replace(' ', '_')}_components.png"
        self.visualizer.create_component_breakdown(
            location,
            priority_results,
            component_viz_path
        )

        # 3. Summary statistics (JSON format with critical spot coordinates)
        import json

        stats_path = location_dir / f"{location.name.lower().replace(' ', '_')}_summary.json"
        summary_data = self.visualizer.create_summary_statistics(
            location,
            priority_results
        )

        with open(stats_path, 'w') as f:
            json.dump(summary_data, f, indent=2)

        logger.debug(f"  Outputs saved to: {location_dir}")

        return location
