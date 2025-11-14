# Ground-Level Tree Detection

This module provides ground-level tree detection capabilities using Google Street View imagery and YOLO object detection.

## Overview

The `ground_tree_detector` module downloads Street View panoramas at specified GPS coordinates and uses a YOLO model (`best.pt`) to detect existing trees at ground level. This complements the aerial analysis by providing street-level validation of tree presence.

## Key Features

- **Street View Integration**: Downloads panoramic images from Google Street View API
- **YOLO Detection**: Uses trained YOLO model to detect trees in Street View images
- **Async Support**: Asynchronous operations for efficient processing
- **Batch Analysis**: Analyze multiple critical spots in sequence
- **Detailed Results**: Returns bounding boxes, confidence scores, and metadata

## Requirements

### Dependencies

```bash
pip install streetview ultralytics pillow numpy
```

### YOLO Model

You need a trained YOLO model file named `best.pt` that can detect trees. The model should be trained to recognize the "tree" class in street-level imagery.

### API Key

A valid Google Maps API key with Street View Static API enabled is required.

## Usage

### Basic Usage - Single Location

```python
import asyncio
from urban_tree_planting.core.ground_tree_detector import create_detector

async def analyze_location():
    # Initialize detector
    detector = create_detector(
        api_key="your_google_maps_api_key",
        model_path="best.pt"
    )
    
    # Analyze a location
    result = await detector.analyze_location(
        lat=3.13792463037415,
        lon=101.62946855487311,
        confidence_threshold=0.5
    )
    
    print(f"Trees detected: {result['total_trees']}")
    print(f"Has trees: {result['has_existing_trees']}")
    print(f"Average confidence: {result['average_confidence']}")
    
    return result

# Run
asyncio.run(analyze_location())
```

### Analyzing Multiple Critical Spots

```python
import asyncio
from urban_tree_planting.core.ground_tree_detector import create_detector

async def analyze_critical_spots():
    detector = create_detector(
        api_key="your_google_maps_api_key",
        model_path="best.pt"
    )
    
    # Define critical spots (from aerial analysis)
    critical_spots = [
        {
            'lat': 3.13792,
            'lon': 101.62946,
            'priority_score': 85,
            'vegetation_deficit': 0.7,
            'area_name': 'Spot 1'
        },
        {
            'lat': 3.138,
            'lon': 101.630,
            'priority_score': 82,
            'vegetation_deficit': 0.65,
            'area_name': 'Spot 2'
        }
    ]
    
    # Analyze top 3-5 spots
    results = await detector.analyze_critical_spots(
        critical_spots=critical_spots,
        max_spots=5,  # Analyze top 5 spots
        confidence_threshold=0.5
    )
    
    for i, result in enumerate(results, 1):
        print(f"\nSpot {i}:")
        print(f"  Location: {result['location']}")
        print(f"  Trees: {result['total_trees']}")
        print(f"  Has existing trees: {result['has_existing_trees']}")
    
    return results

asyncio.run(analyze_critical_spots())
```

### Saving Cropped Tree Images

```python
from pathlib import Path

result = await detector.analyze_location(
    lat=3.13792,
    lon=101.62946,
    save_crops=True,
    output_dir=Path("./detected_trees")
)
```

## API Reference

### `GroundLevelDetector`

Main class for ground-level tree detection.

#### Constructor

```python
detector = GroundLevelDetector(api_key: str, model_path: Optional[str] = None)
```

**Parameters:**
- `api_key` (str): Google Maps API key
- `model_path` (Optional[str]): Path to YOLO model file (default: "best.pt")

#### Methods

##### `analyze_location(lat, lon, confidence_threshold=0.5, save_crops=False, output_dir=None)`

Analyze a single location for trees.

**Parameters:**
- `lat` (float): Latitude coordinate
- `lon` (float): Longitude coordinate
- `confidence_threshold` (float): Minimum detection confidence (0-1, default: 0.5)
- `save_crops` (bool): Whether to save cropped tree images
- `output_dir` (Optional[Path]): Directory to save crops

**Returns:**
```python
{
    'location': {'lat': float, 'lon': float},
    'image_downloaded': bool,
    'total_trees': int,
    'detections': [
        {
            'bbox': [x1, y1, x2, y2],
            'confidence': float,
            'area': float,
            'image_path': Optional[str]
        },
        ...
    ],
    'average_confidence': float,
    'has_existing_trees': bool
}
```

##### `analyze_critical_spots(critical_spots, max_spots=None, confidence_threshold=0.5, save_crops=False, output_dir=None)`

Analyze multiple critical spots.

**Parameters:**
- `critical_spots` (List[Dict]): List of spots with 'lat', 'lon', and optional metadata
- `max_spots` (Optional[int]): Maximum number to analyze (default: analyze all)
- `confidence_threshold` (float): Minimum detection confidence
- `save_crops` (bool): Whether to save cropped images
- `output_dir` (Optional[Path]): Directory to save crops

**Returns:** List of analysis results (one per spot)

### Helper Functions

#### `create_detector(api_key, model_path=None)`

Factory function to create a detector instance.

#### `analyze_spot(lat, lon, api_key, model_path=None)`

Convenience function to analyze a single spot without creating a detector object.

## Integration with Aerial Analysis

The ground-level detector is designed to complement the aerial analysis pipeline:

1. **Aerial Analysis** → Identifies high-priority areas from satellite imagery
2. **Extract Critical Spots** → Select top 3-5 spots with priority scores 80-100
3. **Ground-Level Detection** → Validate existing tree presence at street level
4. **Combined Recommendations** → Merge aerial + ground insights

### Example Integration

```python
# Step 1: Get critical spots from aerial analysis
from urban_tree_planting.pipeline.processor import TreePlantingProcessor

processor = TreePlantingProcessor()
aerial_result = await processor.process_location("Kuala Lumpur")

# Step 2: Extract high-priority spots
critical_spots = [
    spot for spot in aerial_result['critical_spots'] 
    if spot['priority_score'] >= 80
][:5]  # Top 5 spots

# Step 3: Ground-level detection
from urban_tree_planting.core.ground_tree_detector import create_detector

detector = create_detector(api_key="your_key", model_path="best.pt")
ground_results = await detector.analyze_critical_spots(
    critical_spots=critical_spots,
    max_spots=5
)

# Step 4: Combine insights
for aerial_spot, ground_result in zip(critical_spots, ground_results):
    print(f"Spot: {aerial_spot['area_name']}")
    print(f"  Aerial priority: {aerial_spot['priority_score']}")
    print(f"  Vegetation deficit: {aerial_spot['vegetation_deficit']}")
    print(f"  Ground-level trees: {ground_result['total_trees']}")
    print(f"  Recommendation: ", end="")
    
    if ground_result['has_existing_trees']:
        print("Focus on maintenance and diversity")
    else:
        print("High priority for new plantings")
```

## Model Requirements

The YOLO model (`best.pt`) should be trained to detect trees in street-level imagery. Key characteristics:

- **Input**: Street View panoramic images
- **Output**: Bounding boxes for "tree" class
- **Format**: YOLOv8 or compatible format
- **Training**: Should handle various tree types, seasons, and urban environments

## Troubleshooting

### No Street View imagery available

Some locations don't have Street View coverage. The detector will log warnings and return `image_downloaded: false` in results.

### Import errors for streetview or ultralytics

Ensure dependencies are installed:
```bash
pip install streetview ultralytics
```

### YOLO model not found

Ensure `best.pt` is in the correct location or specify the full path:
```python
detector = create_detector(api_key="key", model_path="/path/to/best.pt")
```

### API key issues

Verify your Google Maps API key has the Street View Static API enabled in Google Cloud Console.

## Example Output

```json
{
  "location": {
    "lat": 3.13792463037415,
    "lon": 101.62946855487311
  },
  "image_downloaded": true,
  "total_trees": 5,
  "detections": [
    {
      "bbox": [120, 150, 280, 450],
      "confidence": 0.89,
      "area": 48000.0
    },
    {
      "bbox": [350, 180, 480, 420],
      "confidence": 0.76,
      "area": 31200.0
    }
  ],
  "average_confidence": 0.825,
  "has_existing_trees": true
}
```

## Performance Considerations

- **Async Operations**: Use `await` for I/O operations (Street View downloads)
- **Model Loading**: YOLO model is lazy-loaded on first use
- **Batch Processing**: Process multiple spots sequentially to avoid API rate limits
- **Image Size**: Street View images are downloaded at 640x640 resolution

## Future Enhancements

- Multi-angle analysis (currently single panorama per location)
- Tree species identification integration (FloraSense)
- Confidence threshold tuning based on environment
- Caching of Street View imagery
- Parallel processing of multiple locations

## License

Part of the ReLeaf urban tree planting analysis system.
