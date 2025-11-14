"""
Geographic and geometric utility functions

Contains coordinate conversions, bounding box calculations,
and other geometric operations.
"""

import numpy as np


def meters_to_degrees(meters_north, meters_east, center_lat):
    """
    Convert meters to degrees at given latitude

    Args:
        meters_north: Distance in meters (North-South direction)
        meters_east: Distance in meters (East-West direction)
        center_lat: Center latitude in degrees

    Returns:
        tuple: (lat_offset, lon_offset) in degrees

    Note:
        - 1 degree latitude ≈ 111,000 meters (constant)
        - 1 degree longitude varies by latitude (cos correction needed)
    """
    lat_offset = meters_north / 111000
    lon_offset = meters_east / (111000 * np.cos(np.radians(center_lat)))
    return lat_offset, lon_offset


def degrees_to_meters(lat_offset, lon_offset, center_lat):
    """
    Convert degrees to meters at given latitude

    Args:
        lat_offset: Latitude offset in degrees
        lon_offset: Longitude offset in degrees
        center_lat: Center latitude in degrees

    Returns:
        tuple: (meters_north, meters_east)
    """
    meters_north = lat_offset * 111000
    meters_east = lon_offset * 111000 * np.cos(np.radians(center_lat))
    return meters_north, meters_east


def calculate_image_bounds(center_lat, center_lon, zoom, image_width, image_height, scale=2):
    """
    Calculate geographic bounds of Google Maps satellite image

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        zoom: Google Maps zoom level (18 recommended)
        image_width: Image width in pixels
        image_height: Image height in pixels
        scale: Scale factor (1 or 2, default: 2)

    Returns:
        tuple: (min_lon, min_lat, max_lon, max_lat) geographic bounds

    Note:
        The scale parameter affects download area:
        - scale=2: Standard coverage (~640m diameter at zoom 18)
        - scale=3: 1.5x larger area (for capturing distant highways)
        - scale=4: 2x larger area
    """
    effective_width = image_width * scale
    effective_height = image_height * scale

    # Calculate meters per pixel at this zoom level and latitude
    # Web Mercator formula: meters_per_pixel = 156543.03392 * cos(lat) / (2^zoom)
    meters_per_pixel = 156543.03392 * np.cos(np.radians(center_lat)) / (2 ** zoom)

    # Calculate half-width and half-height in meters
    width_meters = (effective_width / 2) * meters_per_pixel
    height_meters = (effective_height / 2) * meters_per_pixel

    # Convert to degree offsets
    lat_offset = height_meters / 111000
    lon_offset = width_meters / (111000 * np.cos(np.radians(center_lat)))

    # Return bounding box (min_lon, min_lat, max_lon, max_lat)
    return (
        center_lon - lon_offset,  # min_lon (west)
        center_lat - lat_offset,  # min_lat (south)
        center_lon + lon_offset,  # max_lon (east)
        center_lat + lat_offset   # max_lat (north)
    )


def latlon_to_pixel(lat, lon, min_lat, max_lat, min_lon, max_lon, img_height, img_width):
    """
    Convert lat/lon coordinates to pixel coordinates

    Args:
        lat: Latitude to convert
        lon: Longitude to convert
        min_lat, max_lat: Latitude bounds of image
        min_lon, max_lon: Longitude bounds of image
        img_height: Image height in pixels
        img_width: Image width in pixels

    Returns:
        tuple: (x_pixel, y_pixel) pixel coordinates

    Note:
        - (0, 0) is top-left corner
        - x increases to the right
        - y increases downward
    """
    # Normalize to 0-1 range
    x_norm = (lon - min_lon) / (max_lon - min_lon)
    y_norm = (max_lat - lat) / (max_lat - min_lat)  # Inverted because y increases downward

    # Convert to pixel coordinates
    x_pixel = int(x_norm * img_width)
    y_pixel = int(y_norm * img_height)

    return (x_pixel, y_pixel)


def pixel_to_latlon(x_pixel, y_pixel, min_lat, max_lat, min_lon, max_lon, img_height, img_width):
    """
    Convert pixel coordinates to lat/lon coordinates

    Args:
        x_pixel: X pixel coordinate
        y_pixel: Y pixel coordinate
        min_lat, max_lat: Latitude bounds of image
        min_lon, max_lon: Longitude bounds of image
        img_height: Image height in pixels
        img_width: Image width in pixels

    Returns:
        tuple: (lat, lon) geographic coordinates
    """
    # Normalize pixel coordinates to 0-1
    x_norm = x_pixel / img_width
    y_norm = y_pixel / img_height

    # Convert to geographic coordinates
    lon = min_lon + x_norm * (max_lon - min_lon)
    lat = max_lat - y_norm * (max_lat - min_lat)  # Inverted because y increases downward

    return (lat, lon)
