"""
Example script demonstrating how to use the GroundLevelDetector for tree detection.

This script shows how to:
1. Initialize the detector with API key and model path
2. Analyze a single location
3. Analyze multiple critical spots
"""

import asyncio
import os
from pathlib import Path
import sys

# Add parent directory to path to import urban_tree_planting
sys.path.insert(0, str(Path(__file__).parent.parent))

from urban_tree_planting.core.ground_tree_detector import create_detector


async def analyze_single_location_example():
    """Example: Analyze a single location for ground-level trees."""
    
    # Configuration
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "your_api_key_here")
    model_path = "best.pt"  # Path to YOLO model
    
    # Menara LGB coordinates (from notebook)
    lat = 3.13792463037415
    lon = 101.62946855487311
    
    print(f"\n{'='*60}")
    print("EXAMPLE 1: Analyzing Single Location")
    print(f"{'='*60}")
    print(f"Location: ({lat}, {lon})")
    print(f"Model: {model_path}")
    
    # Create detector
    detector = create_detector(api_key, model_path)
    
    # Analyze the location
    result = await detector.analyze_location(
        lat=lat,
        lon=lon,
        confidence_threshold=0.5,
        save_crops=False
    )
    
    # Print results
    print(f"\nResults:")
    print(f"  Image downloaded: {result['image_downloaded']}")
    print(f"  Total trees detected: {result['total_trees']}")
    print(f"  Average confidence: {result['average_confidence']}")
    print(f"  Has existing trees: {result['has_existing_trees']}")
    
    if result['total_trees'] > 0:
        print(f"\n  Tree detections:")
        for i, detection in enumerate(result['detections'][:3], 1):  # Show first 3
            print(f"    Tree {i}:")
            print(f"      Confidence: {detection['confidence']}")
            print(f"      Bounding box: {detection['bbox']}")
            print(f"      Area: {detection['area']:.2f} pixels²")
    
    return result


async def analyze_critical_spots_example():
    """Example: Analyze multiple critical spots."""
    
    # Configuration
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "your_api_key_here")
    model_path = "best.pt"
    
    # Example critical spots (you would get these from aerial analysis)
    critical_spots = [
        {
            'lat': 3.13792463037415,
            'lon': 101.62946855487311,
            'priority_score': 85,
            'vegetation_deficit': 0.7,
            'bare_land_pct': 0.4,
            'area_name': 'Menara LGB Area'
        },
        {
            'lat': 3.138,
            'lon': 101.630,
            'priority_score': 82,
            'vegetation_deficit': 0.65,
            'bare_land_pct': 0.38,
            'area_name': 'Nearby Location'
        }
    ]
    
    print(f"\n{'='*60}")
    print("EXAMPLE 2: Analyzing Critical Spots")
    print(f"{'='*60}")
    print(f"Total spots to analyze: {len(critical_spots)}")
    print(f"Analyzing top 2 spots")
    
    # Create detector
    detector = create_detector(api_key, model_path)
    
    # Analyze critical spots
    results = await detector.analyze_critical_spots(
        critical_spots=critical_spots,
        max_spots=2,
        confidence_threshold=0.5,
        save_crops=False
    )
    
    # Print results
    print(f"\nAnalyzed {len(results)} spots:\n")
    for i, result in enumerate(results, 1):
        spot_info = result['spot_info']
        print(f"Spot {i}: {spot_info.get('area_name', 'Unknown')}")
        print(f"  Location: ({result['location']['lat']}, {result['location']['lon']})")
        print(f"  Priority Score: {spot_info.get('priority_score')}")
        print(f"  Trees detected: {result['total_trees']}")
        print(f"  Has existing trees: {result['has_existing_trees']}")
        print(f"  Average confidence: {result['average_confidence']}")
        print()
    
    return results


async def main():
    """Run all examples."""
    
    print("\n" + "="*60)
    print("Ground-Level Tree Detection Examples")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\n⚠️  WARNING: GOOGLE_MAPS_API_KEY not set!")
        print("Set the environment variable before running this script.")
        print("Example: export GOOGLE_MAPS_API_KEY='your_actual_key'")
        return
    
    # Check for YOLO model
    if not Path("best.pt").exists():
        print("\n⚠️  WARNING: YOLO model 'best.pt' not found!")
        print("Place the YOLO model file in the current directory.")
        return
    
    try:
        # Run examples
        await analyze_single_location_example()
        await analyze_critical_spots_example()
        
        print("\n" + "="*60)
        print("✅ Examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
