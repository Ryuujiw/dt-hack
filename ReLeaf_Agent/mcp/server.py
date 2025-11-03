import asyncio
import logging
import os
from typing import Dict

from fastmcp import FastMCP
from src.get_areas_where_more_trees_can_be_planted import get_areas_where_more_tree_can_be_planted

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("ReLeaf Tree Planting MCP Server")


@mcp.tool()
def get_areas_where_more_trees_can_be_planted(
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
    return get_areas_where_more_tree_can_be_planted(
        north=north,
        south=south,
        east=east,
        west=west,
        tree_buffer_meters=tree_buffer_meters,
        output_filename=output_filename
    )


if __name__ == "__main__":
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8080),
        )
    )
