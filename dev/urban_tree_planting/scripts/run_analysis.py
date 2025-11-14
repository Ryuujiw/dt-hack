#!/usr/bin/env python3
"""
Command-line interface for urban tree planting analysis

Usage:
    # Process all locations
    python scripts/run_analysis.py

    # Process specific location
    python scripts/run_analysis.py --location-name "Aster Hill"

    # Custom output directory
    python scripts/run_analysis.py --output /path/to/output

    # Verbose logging
    python scripts/run_analysis.py --verbose

    # Custom locations file
    python scripts/run_analysis.py --locations custom_locations.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.processor import TreePlantingPipeline
from models.location import Location
from config.settings import LOCATIONS_FILE, OUTPUT_DIR
from utils.logger import setup_logger, logger


def load_locations(filepath: Path) -> list:
    """
    Load locations from JSON file

    Args:
        filepath: Path to locations.json file

    Returns:
        list: List of Location objects

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        KeyError: If required fields missing
    """
    logger.info(f"Loading locations from: {filepath}")

    if not filepath.exists():
        raise FileNotFoundError(f"Locations file not found: {filepath}")

    with open(filepath, 'r') as f:
        data = json.load(f)

    if 'locations' not in data:
        raise KeyError("JSON file must contain 'locations' array")

    locations = []
    for loc_data in data['locations']:
        # Validate required fields
        required_fields = ['name', 'description', 'lat', 'lon']
        missing = [f for f in required_fields if f not in loc_data]
        if missing:
            raise KeyError(f"Location missing required fields: {missing}")

        location = Location(
            name=loc_data['name'],
            description=loc_data['description'],
            lat=loc_data['lat'],
            lon=loc_data['lon']
        )
        locations.append(location)

    logger.info(f"✓ Loaded {len(locations)} locations")
    return locations


def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        description="Urban Tree Planting Recommendations Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all locations from default file
  python scripts/run_analysis.py

  # Process specific location
  python scripts/run_analysis.py --location-name "Aster Hill"

  # Use custom locations file
  python scripts/run_analysis.py --locations my_locations.json

  # Custom output directory with verbose logging
  python scripts/run_analysis.py --output ./results --verbose
        """
    )

    parser.add_argument(
        '--locations',
        type=Path,
        default=LOCATIONS_FILE,
        help=f'Path to locations JSON file (default: {LOCATIONS_FILE})'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=OUTPUT_DIR,
        help=f'Output directory for results (default: {OUTPUT_DIR})'
    )

    parser.add_argument(
        '--location-name',
        type=str,
        help='Process only this location by name (optional)'
    )

    parser.add_argument(
        '--delay',
        type=int,
        help='Seconds to wait between locations (default: from settings)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )

    parser.add_argument(
        '--log-file',
        type=Path,
        help='Save logs to file (optional)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logger(verbose=args.verbose, log_file=args.log_file)

    logger.info("=" * 70)
    logger.info("URBAN TREE PLANTING ANALYSIS - PRODUCTION")
    logger.info("=" * 70)

    try:
        # Load locations
        all_locations = load_locations(args.locations)

        # Filter if specific location requested
        if args.location_name:
            locations = [
                loc for loc in all_locations
                if loc.name.lower() == args.location_name.lower()
            ]
            if not locations:
                logger.error(f"Location '{args.location_name}' not found in {args.locations}")
                logger.info(f"Available locations:")
                for loc in all_locations:
                    logger.info(f"  - {loc.name}")
                return 1
            logger.info(f"Processing single location: {locations[0].name}")
        else:
            locations = all_locations
            logger.info(f"Processing all {len(locations)} locations")

        # Create output directory
        args.output.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {args.output}")

        # Create and run pipeline
        pipeline = TreePlantingPipeline(output_dir=args.output)

        if len(locations) == 1:
            # Single location - no batch delay
            result = pipeline.process_location(locations[0])
            results = [result]
        else:
            # Multiple locations - batch processing
            results = pipeline.process_batch(locations, delay_between=args.delay)

        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ ANALYSIS COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"Processed: {len(results)}/{len(locations)} locations")
        logger.info(f"Results saved to: {args.output}")

        for result in results:
            location_dir = args.output / result.name.lower().replace(' ', '_')
            logger.info(f"\n{result.name}:")
            logger.info(f"  📁 {location_dir}")
            logger.info(f"  📊 Analysis visualization (PNG)")
            logger.info(f"  📈 Component breakdown (PNG)")
            logger.info(f"  📍 Summary with critical spot coordinates (JSON)")

        logger.info("\n" + "=" * 70 + "\n")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in locations file: {e}")
        return 1

    except KeyError as e:
        logger.error(f"Invalid locations file format: {e}")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
