"""
Vegetation and shadow detector

Detects vegetation using NDVI and shadows using brightness/saturation analysis.
Vegetation-aware shadow detection excludes green areas from shadow classification.
"""

import numpy as np
import cv2
from PIL import Image

from config.settings import (
    NDVI_THRESHOLD,
    MIN_VEGETATION_BRIGHTNESS,
    SHADOW_BRIGHTNESS_THRESHOLD,
    SHADOW_DESATURATION_THRESHOLD,
    SHADOW_VERY_DARK_THRESHOLD,
    SHADOW_MIN_SIZE_PIXELS,
)
from utils.logger import logger


class VegetationDetector:
    """
    Detects vegetation and shadows from satellite imagery

    Uses:
    - NDVI (Normalized Difference Vegetation Index) for vegetation
    - HSV brightness and saturation for shadows
    - Morphological operations for cleanup
    """

    def __init__(self):
        """Initialize detector"""
        logger.debug("VegetationDetector initialized")

    def detect(self, img):
        """
        Comprehensive vegetation-aware shadow detection

        Args:
            img: PIL Image in RGB format

        Returns:
            tuple: (shadow_mask, vegetation_mask, ndvi)
                - shadow_mask: Boolean array of shadow pixels
                - vegetation_mask: Boolean array of vegetation pixels
                - ndvi: Float array of NDVI values

        Process:
        1. Detect vegetation using NDVI and brightness
        2. Detect shadows excluding vegetation areas
        3. Clean up small noise artifacts
        """
        logger.debug("Detecting vegetation and shadows...")

        # Step 1: Detect vegetation
        vegetation_mask, ndvi = self._detect_vegetation(img)

        # Step 2: Detect shadows (excluding vegetation)
        shadow_very_dark = self._detect_shadows_very_dark(img, vegetation_mask)
        shadow_simple = self._detect_shadows_simple(img, vegetation_mask)

        # Combine shadow masks
        shadow_combined = shadow_very_dark | shadow_simple

        # Step 3: Cleanup
        shadow_cleaned = self._cleanup_shadows(shadow_combined)

        # Calculate statistics
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        veg_pct = np.sum(vegetation_mask) / total_pixels * 100
        shadow_pct = np.sum(shadow_cleaned) / total_pixels * 100

        logger.debug(f"  Vegetation: {veg_pct:.1f}%, Shadows: {shadow_pct:.1f}%")

        return shadow_cleaned, vegetation_mask, ndvi

    def _detect_vegetation(self, img,
                          ndvi_threshold=NDVI_THRESHOLD,
                          min_brightness=MIN_VEGETATION_BRIGHTNESS):
        """
        Detect vegetation using NDVI AND brightness requirement

        NDVI = (Green - Red) / (Green + Red)

        Vegetation must be:
        1. Green (NDVI > threshold)
        2. Not extremely dark (V > min_brightness)

        Args:
            img: PIL Image
            ndvi_threshold: Minimum NDVI value for vegetation
            min_brightness: Minimum brightness value (0-255)

        Returns:
            tuple: (vegetation_mask, ndvi)
        """
        img_array = np.array(img)

        # Calculate NDVI
        green = img_array[:, :, 1].astype(float)
        red = img_array[:, :, 0].astype(float)
        ndvi = (green - red) / (green + red + 1e-8)

        # Get brightness (Value channel from HSV)
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        v = hsv[:, :, 2]

        # Vegetation must be green AND not extremely dark
        vegetation_mask = (ndvi > ndvi_threshold) & (v > min_brightness)

        return vegetation_mask, ndvi

    def _detect_shadows_simple(self, img, vegetation_mask):
        """
        Simple shadow detection EXCLUDING vegetation areas

        Shadows are:
        - Dark (low brightness)
        - Desaturated (low saturation)
        - NOT vegetation

        Args:
            img: PIL Image
            vegetation_mask: Boolean array of vegetation pixels

        Returns:
            Boolean array: Shadow mask
        """
        img_array = np.array(img)
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        v = hsv[:, :, 2]  # Brightness
        s = hsv[:, :, 1]  # Saturation

        # Shadows are dark and desaturated
        dark = v < SHADOW_BRIGHTNESS_THRESHOLD
        desaturated = s < SHADOW_DESATURATION_THRESHOLD

        # Must be dark AND desaturated AND NOT vegetation
        shadow = dark & desaturated & (~vegetation_mask)

        return shadow

    def _detect_shadows_very_dark(self, img, vegetation_mask):
        """
        Detect VERY dark areas EXCLUDING vegetation

        Args:
            img: PIL Image
            vegetation_mask: Boolean array of vegetation pixels

        Returns:
            Boolean array: Shadow mask
        """
        img_array = np.array(img)
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        v = hsv[:, :, 2]

        # Very dark areas
        very_dark = v < SHADOW_VERY_DARK_THRESHOLD

        # Must NOT be vegetation
        shadow = very_dark & (~vegetation_mask)

        return shadow

    def _cleanup_shadows(self, shadow_mask):
        """
        Clean up shadow mask using morphological operations

        1. Closing operation to fill small holes
        2. Remove small noise artifacts (< min_size pixels)

        Args:
            shadow_mask: Boolean array

        Returns:
            Boolean array: Cleaned shadow mask
        """
        # Light cleanup with morphological closing
        kernel = np.ones((3, 3), np.uint8)
        shadow_combined = cv2.morphologyEx(
            shadow_mask.astype(np.uint8),
            cv2.MORPH_CLOSE,
            kernel,
            iterations=1
        )

        # Remove small noise (< SHADOW_MIN_SIZE_PIXELS pixels)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            shadow_combined,
            connectivity=8
        )

        shadow_cleaned = np.zeros_like(shadow_combined, dtype=bool)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= SHADOW_MIN_SIZE_PIXELS:
                shadow_cleaned[labels == i] = True

        return shadow_cleaned

    def calculate_shadow_intensity(self, img):
        """
        Calculate shadow intensity across the image

        Args:
            img: PIL Image

        Returns:
            np.ndarray: Float array (0.0 = no shadow, 1.0 = full shadow)
        """
        img_array = np.array(img)
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        v = hsv[:, :, 2]

        # Normalize brightness (0-255 -> 0.0-1.0)
        v_norm = v.astype(float) / 255.0

        # Shadow intensity = 1 - brightness (darker = higher intensity)
        shadow_intensity = 1.0 - v_norm

        # Clamp to 0-1
        shadow_intensity = np.clip(shadow_intensity, 0.0, 1.0)

        return shadow_intensity
