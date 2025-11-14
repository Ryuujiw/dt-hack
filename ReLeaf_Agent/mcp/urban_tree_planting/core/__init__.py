"""
Core processing modules for urban tree planting analysis

Contains the main processing logic:
- Downloader: Download satellite images and OSM data
- Transformer: Apply geometric transformations
- Detector: Detect vegetation and shadows
- MaskGenerator: Create pixel masks from geometries
- PriorityCalculator: Calculate planting priority scores
- Visualizer: Generate output visualizations
- GroundLevelDetector: Detect existing trees from Street View imagery
"""

from .downloader import DataDownloader
from .transformer import GeometryTransformer
from .detector import VegetationDetector
from .mask_generator import MaskGenerator
from .priority_calculator import PriorityCalculator
from .visualizer import ResultVisualizer
from .ground_tree_detector import GroundLevelDetector, create_detector, analyze_spot

__all__ = [
    'DataDownloader',
    'GeometryTransformer',
    'VegetationDetector',
    'MaskGenerator',
    'PriorityCalculator',
    'ResultVisualizer',
    'GroundLevelDetector',
    'create_detector',
    'analyze_spot',
]
