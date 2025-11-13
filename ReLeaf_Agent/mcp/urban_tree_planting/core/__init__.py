"""
Core processing modules for urban tree planting analysis

Contains the main processing logic:
- Downloader: Download satellite images and OSM data
- Transformer: Apply geometric transformations
- Detector: Detect vegetation and shadows
- MaskGenerator: Create pixel masks from geometries
- PriorityCalculator: Calculate planting priority scores
- Visualizer: Generate output visualizations
"""

from .downloader import DataDownloader
from .transformer import GeometryTransformer
from .detector import VegetationDetector
from .mask_generator import MaskGenerator
from .priority_calculator import PriorityCalculator
from .visualizer import ResultVisualizer

__all__ = [
    'DataDownloader',
    'GeometryTransformer',
    'VegetationDetector',
    'MaskGenerator',
    'PriorityCalculator',
    'ResultVisualizer',
]
