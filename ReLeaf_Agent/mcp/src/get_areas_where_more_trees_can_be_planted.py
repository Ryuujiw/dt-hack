import logging
import tempfile
from typing import Dict

import osmnx as ox
import geopandas as gpd
import folium

logger = logging.getLogger(__name__)


def get_areas_where_more_tree_can_be_planted(
    north: float = 3.1505,
    south: float = 3.128,
    east: float = 101.641,
    west: float = 101.615,
    tree_buffer_meters: float = 2.0,
    output_filename: str = "plantable_areas_map.html"
) -> Dict[str, any]:
    """
    Identifies areas where trees can be planted by analyzing OSM data
    for parks, grass areas, and existing trees. Creates a map showing
    plantable areas and suggests appropriate trees.

    Args:
        north: Northern boundary latitude
        south: Southern boundary latitude
        east: Eastern boundary longitude
        west: Western boundary longitude
        tree_buffer_meters: Buffer distance around existing trees (meters)
        output_filename: Name for the output HTML map file

    Returns:
        Dictionary with analysis results and map file path
    """
    try:
        bbox = (west, south, east, north)
        
        # Fetch plantable areas from OSM
        tags = {
            'leisure': 'park',
            'landuse': 'grass',
            'natural': 'grass'
        }

        plantable_areas = gpd.GeoDataFrame(columns=['geometry'], geometry=[])
        try:
            plantable_areas = ox.features_from_bbox(bbox, tags)
            plantable_areas = plantable_areas.to_crs(epsg=3857)
            plantable_areas = plantable_areas[
                plantable_areas.geometry.notnull()
            ]
            # Explode mixed geometries
            plantable_areas = plantable_areas.explode(
                index_parts=False
            ).reset_index(drop=True)
            valid_types = ['Polygon', 'MultiPolygon']
            plantable_areas = plantable_areas[
                plantable_areas.geometry.type.isin(valid_types)
            ]
            logger.info(f"Plantable areas found: {len(plantable_areas)}")
        except Exception as e:
            logger.error(f"Error fetching plantable areas: {e}")

        # Fetch existing trees (points) from OSM
        tree_tags = {'natural': 'tree'}
        existing_trees = gpd.GeoDataFrame(columns=['geometry'], geometry=[])
        try:
            existing_trees = ox.features_from_bbox(bbox, tree_tags)
            existing_trees = existing_trees.to_crs(epsg=3857)
            existing_trees = existing_trees[
                existing_trees.geometry.notnull()
            ]
            existing_trees = existing_trees[
                existing_trees.geometry.type == 'Point'
            ]
            logger.info(f"Existing trees found: {len(existing_trees)}")
        except Exception as e:
            logger.error(f"Error fetching existing trees: {e}")

        # Remove areas too close to existing trees
        original_count = len(plantable_areas)
        if not existing_trees.empty and not plantable_areas.empty:
            existing_trees['geometry'] = existing_trees.geometry.buffer(
                tree_buffer_meters
            )
            plantable_areas = gpd.overlay(
                plantable_areas, existing_trees, how='difference'
            )
            msg = (f"Plantable areas after removing existing trees: "
                   f"{len(plantable_areas)}")
            logger.info(msg)

        def suggest_tree(area_m2):
            """Function to suggest tree based on plot size (m²)"""
            if area_m2 < 5:
                return "Hibiscus"  # small shrub
            elif area_m2 < 20:
                return "Plumeria"
            elif area_m2 < 50:
                return "Frangipani"
            elif area_m2 < 100:
                return "Angsana"
            else:
                return "Rain Tree"  # large tropical tree

        # Calculate area and assign tree suggestions
        if not plantable_areas.empty:
            plantable_areas['area_m2'] = plantable_areas.geometry.area
            plantable_areas['suggested_tree'] = plantable_areas[
                'area_m2'
            ].apply(suggest_tree)

        # Convert to WGS84 for Folium
        plantable_areas = plantable_areas.to_crs(epsg=4326)
        center_lat = (north + south) / 2
        center_lon = (east + west) / 2

        # Create Folium map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=16,
            tiles='CartoDB positron'
        )

        # Convert buffered existing trees to WGS84 for Folium
        if not existing_trees.empty:
            existing_trees = existing_trees.to_crs(epsg=4326)

        # Add plantable areas (blue) to map
        for _, row in plantable_areas.iterrows():
            tooltip_text = (f"Area: {row['area_m2']:.1f} m²\n"
                            f"Suggested tree: {row['suggested_tree']}")
            folium.GeoJson(
                row.geometry,
                style_function=lambda feature, color="blue": {
                    'fillColor': color,
                    'color': 'darkblue',
                    'weight': 1,
                    'fillOpacity': 0.5
                },
                tooltip=tooltip_text
            ).add_to(m)

        # Add existing trees (green) to map
        for _, row in existing_trees.iterrows():
            folium.GeoJson(
                row.geometry,
                style_function=lambda feature: {
                    "fillColor": "green",
                    "color": "green",
                    "weight": 1,
                    "fillOpacity": 0.5
                },
                tooltip="Existing tree"
            ).add_to(m)

        # Save map to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False
        ) as f:
            output_path = f.name
            m.save(output_path)

        logger.info(f"Map saved successfully at {output_path}")

        # Calculate summary statistics
        total_plantable_area = (
            plantable_areas['area_m2'].sum()
            if not plantable_areas.empty else 0
        )

        # Group by suggested trees
        tree_suggestions = {}
        if not plantable_areas.empty:
            tree_counts = plantable_areas['suggested_tree'].value_counts()
            for tree_type, count in tree_counts.items():
                filtered_areas = plantable_areas[
                    plantable_areas['suggested_tree'] == tree_type
                ]
                tree_suggestions[tree_type] = {
                    'count': int(count),
                    'total_area_m2': float(filtered_areas['area_m2'].sum())
                }

        return {
            'success': True,
            'map_file_path': output_path,
            'summary': {
                'total_plantable_areas': len(plantable_areas),
                'total_plantable_area_m2': float(total_plantable_area),
                'existing_trees_count': len(existing_trees),
                'original_areas_found': original_count,
                'tree_suggestions': tree_suggestions
            },
            'bounding_box': {
                'north': north,
                'south': south,
                'east': east,
                'west': west
            }
        }

    except Exception as e:
        logger.error(f"Error in get_areas_where_more_tree_can_be_planted: {e}")
        return {
            'success': False,
            'error': str(e),
            'map_file_path': None
        }
