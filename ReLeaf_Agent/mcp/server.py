import asyncio
import logging
import os
from typing import Dict

from fastmcp import FastMCP

from geocoding_search import GeocodingSearch

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Tree Planting Agent MCP Server on Cloud Run")


@mcp.tool()
def search_all_matching_location_based_on_keyword(keyword) -> Dict[str, tuple]:
    """
    Search for addresses based on a keyword using GeoPy + Nominatim.
    :param keyword: Search term (e.g., 'Menara LGB', 'Menara OBYU')
    :param max_results: Maximum number of results to return
    :return: List of (address, latitude, longitude) tuples
    """
    keyword = keyword.strip()
    try:
        geocoder = GeocodingSearch()
        return geocoder.search_address(keyword)
    except ValueError as e:
        logger.error(f"Error: {e}")
        return {}


@mcp.tool()
def get_areas_where_trees_can_be_planted() -> str:
    """Get information about areas near Menara LGB where trees can be planted."""
    return """Based on the analysis of the Menara LGB area in Kuala Lumpur:

SUITABLE PLANTING AREAS:
• Open green spaces within 500m radius of Menara LGB
• Roadside verges along Jalan Damansara 
• Parking lot perimeters and medians
• Courtyard areas around the building complex
• Walkway corridors that lack shade coverage

RECOMMENDED TREE SPECIES:
• Rain Tree (Samanea saman) - Excellent for shade and flood mitigation
• Angsana (Pterocarpus indicus) - Dense canopy, beautiful flowering
• Yellow Flame (Peltophorum pterocarpum) - Good for medium-sized areas
• Sea Apple (Syzygium grande) - Native species, good for wet areas
• Tembusu (Fagraea fragrans) - Drought tolerant, fragrant flowers

PLANTING CONSIDERATIONS:
• Plant during monsoon season (May-October) for Rain Tree, Angsana, Yellow Flame, Sea Apple
• Plant during dry season (November-April) for Tembusu
• Maintain 30m distance from buildings for large trees
• Consider underground utilities when selecting planting spots
• Ensure adequate water drainage for flood-prone areas"""


if __name__ == "__main__":
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8080),
        )
    )
