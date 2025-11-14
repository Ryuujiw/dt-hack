"""
Ground-level tree detection using Google Street View and YOLO model.

This module downloads Street View panoramas at specified coordinates and uses
YOLO (best.pt) to detect existing trees at ground level.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from PIL import Image
import asyncio
import numpy as np

logger = logging.getLogger(__name__)


class TreeDetection:
    """Represents a single tree detection result."""
    
    def __init__(self, bbox: List[float], confidence: float, image_path: Optional[str] = None):
        """
        Args:
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            confidence: Detection confidence score (0-1)
            image_path: Optional path where cropped tree image is saved
        """
        self.bbox = bbox
        self.confidence = confidence
        self.image_path = image_path
        self.area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'bbox': self.bbox,
            'confidence': round(self.confidence, 3),
            'area': round(self.area, 2),
            'image_path': self.image_path
        }


class GroundLevelDetector:
    """Handles ground-level tree detection from Street View imagery."""
    
    def __init__(self, api_key: str, model_path: Optional[str] = None):
        """
        Initialize the ground-level detector.
        
        Args:
            api_key: Google Maps API key for Street View
            model_path: Path to YOLO model (best.pt). If None, uses default location.
        """
        self.api_key = api_key
        
        # Default model path - looks in /workspace (Cloud Run) or current directory
        if model_path is None:
            # Try Cloud Run location first, fallback to local
            if Path("/workspace/best.pt").exists():
                self.model_path = "/workspace/best.pt"
            else:
                self.model_path = "best.pt"
        else:
            self.model_path = model_path
        
        self._model = None
        
        logger.info(f"Initialized GroundLevelDetector with model: {self.model_path}")
    
    def _load_yolo_model(self):
        """Lazy load YOLO model to save memory."""
        if self._model is None:
            try:
                from ultralytics import YOLO
                self._model = YOLO(self.model_path)
                logger.info(f"Loaded YOLO model from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
                raise
        return self._model
    
    async def download_street_view_panorama(
        self, 
        lat: float, 
        lon: float,
        zoom: int = 5
    ) -> Optional[Image.Image]:
        """
        Download a Street View panorama at the specified coordinates using streetview library.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            zoom: Zoom level for the panorama (0-5, higher = more detail)
            
        Returns:
            PIL Image object or None if download fails
        """
        try:
            from streetview import search_panoramas, get_panorama_async
            
            # Search for available panoramas at this location
            panos = search_panoramas(lat=lat, lon=lon)
            
            if not panos:
                logger.warning(f"No Street View panoramas available at ({lat}, {lon})")
                return None
            
            # Get the first (closest) panorama
            pano_id = panos[0].pano_id
            logger.info(f"Found panorama {pano_id} at ({lat}, {lon})")
            
            # Download the panorama image
            image = await get_panorama_async(pano_id=pano_id, zoom=zoom)
            logger.info(f"Downloaded panorama {pano_id} with zoom={zoom}")
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to download Street View panorama: {e}")
            return None
    
    def detect_trees_in_image(
        self, 
        image: Image.Image, 
        confidence_threshold: float = 0.5,
        save_crops: bool = False,
        output_dir: Optional[Path] = None
    ) -> List[TreeDetection]:
        """
        Detect trees in an image using YOLO model.
        
        Args:
            image: PIL Image to analyze
            confidence_threshold: Minimum confidence score (0-1)
            save_crops: Whether to save cropped tree images
            output_dir: Directory to save cropped images (if save_crops=True)
            
        Returns:
            List of TreeDetection objects
        """
        try:
            model = self._load_yolo_model()
            
            # Run YOLO inference (pass PIL Image directly)
            results = model.predict(source=image, conf=confidence_threshold, verbose=False, save=False)
            
            # Log available classes for debugging
            logger.info(f"YOLO model classes: {model.names}")
            
            detections = []
            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes
                    names = model.names  # mapping: class_id -> class_name
                    
                    logger.info(f"Found {len(boxes)} total detections in image")
                    
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        label = names[cls_id]
                        confidence = float(box.conf[0])
                        
                        logger.info(f"Detection: class='{label}' (id={cls_id}), confidence={confidence:.2f}")
                        
                        # Filter for 'tree' class (try multiple variations)
                        if label.lower() in ["tree", "trees", "plant", "vegetation", "0"]:
                            bbox = box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
                            
                            # Optionally save cropped tree image
                            crop_path = None
                            if save_crops and output_dir:
                                x1, y1, x2, y2 = map(int, bbox)
                                cropped = image.crop((x1, y1, x2, y2))
                                
                                output_dir.mkdir(parents=True, exist_ok=True)
                                crop_path = output_dir / f"tree_{x1}_{y1}.jpg"
                                cropped.save(crop_path)
                                logger.debug(f"Saved cropped tree to {crop_path}")
                            
                            detections.append(TreeDetection(bbox, confidence, str(crop_path) if crop_path else None))
            
            logger.info(f"Detected {len(detections)} trees with confidence >= {confidence_threshold}")
            return detections
            
        except Exception as e:
            logger.error(f"Tree detection failed: {e}")
            return []
    
    async def analyze_location(
        self, 
        lat: float, 
        lon: float,
        confidence_threshold: float = 0.5,
        save_crops: bool = False,
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        Analyze a location for ground-level tree presence.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            confidence_threshold: Minimum confidence for tree detection
            save_crops: Whether to save cropped tree images
            output_dir: Directory to save crops
            
        Returns:
            Dictionary with analysis results:
            {
                'location': {'lat': float, 'lon': float},
                'image_downloaded': bool,
                'total_trees': int,
                'detections': [TreeDetection.to_dict(), ...],
                'average_confidence': float,
                'has_existing_trees': bool
            }
        """
        logger.info(f"Analyzing location ({lat}, {lon})")
        
        # Download Street View panorama
        image = await self.download_street_view_panorama(lat, lon)
        
        if image is None:
            return {
                'location': {'lat': lat, 'lon': lon},
                'image_downloaded': False,
                'total_trees': 0,
                'detections': [],
                'average_confidence': 0.0,
                'has_existing_trees': False,
                'error': 'No Street View imagery available'
            }
        
        # Detect trees in the panorama
        detections = self.detect_trees_in_image(
            image, 
            confidence_threshold=confidence_threshold,
            save_crops=save_crops,
            output_dir=output_dir
        )
        
        # Calculate statistics
        total_trees = len(detections)
        avg_confidence = (sum(d.confidence for d in detections) / total_trees) if total_trees > 0 else 0.0
        has_trees = total_trees > 0
        
        result = {
            'location': {'lat': lat, 'lon': lon},
            'image_downloaded': True,
            'total_trees': total_trees,
            'detections': [d.to_dict() for d in detections],
            'average_confidence': round(avg_confidence, 3),
            'has_existing_trees': has_trees
        }
        
        logger.info(f"Location analysis complete: {total_trees} trees detected (avg confidence: {avg_confidence:.3f})")
        return result
    
    async def analyze_critical_spots(
        self,
        critical_spots: List[Dict],
        max_spots: Optional[int] = None,
        confidence_threshold: float = 0.5,
        save_crops: bool = False,
        output_dir: Optional[Path] = None
    ) -> List[Dict]:
        """
        Analyze multiple critical spots for ground-level tree presence.
        
        Args:
            critical_spots: List of spots with 'lat', 'lon', and optional metadata
            max_spots: Maximum number of spots to analyze (None = analyze all)
            confidence_threshold: Minimum confidence for detections
            save_crops: Whether to save cropped tree images
            output_dir: Directory to save crops
            
        Returns:
            List of analysis results for each spot
        """
        if max_spots:
            spots_to_analyze = critical_spots[:max_spots]
            logger.info(f"Analyzing top {max_spots} of {len(critical_spots)} critical spots")
        else:
            spots_to_analyze = critical_spots
            logger.info(f"Analyzing all {len(critical_spots)} critical spots")
        
        results = []
        for i, spot in enumerate(spots_to_analyze):
            lat = spot.get('lat')
            lon = spot.get('lon')
            
            if lat is None or lon is None:
                logger.warning(f"Skipping spot {i+1} with missing coordinates: {spot}")
                continue
            
            # Analyze this location
            spot_output_dir = output_dir / f"spot_{i+1}" if output_dir else None
            analysis = await self.analyze_location(
                lat, lon,
                confidence_threshold=confidence_threshold,
                save_crops=save_crops,
                output_dir=spot_output_dir
            )
            
            # Add spot metadata
            analysis['spot_info'] = {
                'spot_number': i + 1,
                'priority_score': spot.get('priority_score'),
                'vegetation_deficit': spot.get('vegetation_deficit'),
                'bare_land_pct': spot.get('bare_land_pct'),
                'area_name': spot.get('area_name')
            }
            
            results.append(analysis)
        
        logger.info(f"Completed ground-level analysis for {len(results)} spots")
        return results


def create_detector(api_key: str, model_path: Optional[str] = None) -> GroundLevelDetector:
    """
    Factory function to create a GroundLevelDetector instance.
    
    Args:
        api_key: Google Maps API key
        model_path: Optional path to YOLO model (default: 'best.pt')
        
    Returns:
        Configured GroundLevelDetector instance
    """
    return GroundLevelDetector(api_key, model_path)


async def analyze_spot(lat: float, lon: float, api_key: str, model_path: Optional[str] = None) -> Dict:
    """
    Convenience function to analyze a single spot.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        api_key: Google Maps API key
        model_path: Optional path to YOLO model
        
    Returns:
        Analysis result dictionary
    """
    detector = create_detector(api_key, model_path)
    return await detector.analyze_location(lat, lon)
