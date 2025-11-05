import asyncio
import logging
import os
from typing import Dict, List, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Tree Planting Agent MCP Server on Cloud Run")


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


@mcp.tool()
def get_existing_trees_info() -> str:
    """Get information about existing trees in the Menara LGB area."""
    return """EXISTING TREE INVENTORY NEAR MENARA LGB:

CURRENT TREE COVERAGE:
• Sparse tree coverage around the immediate building area
• Limited shade trees along pedestrian walkways
• Few large canopy trees in parking areas
• Gaps in green coverage along main road frontage

IDENTIFIED GAPS:
• Insufficient shade coverage for pedestrian areas
• Limited natural cooling around building entrances
• Poor air quality buffering from traffic on Jalan Damansara
• Minimal stormwater management through urban forestry

IMPROVEMENT OPPORTUNITIES:
• Add 15-20 medium to large canopy trees
• Focus on high-traffic pedestrian zones
• Create green corridors connecting to nearby parks
• Enhance building microclimatic conditions
• Improve urban heat island effect mitigation"""


@mcp.tool()
def get_tree_care_instructions(species_name: str) -> str:
    """Get specific care instructions for a tree species."""
    care_guide = {
        "Rain Tree": "Water deeply 2-3 times per week during establishment. Requires minimal pruning. Very hardy once established. Monitor for pests during flowering season.",
        "Angsana": "Regular watering during dry periods. Prune annually after flowering to maintain shape. Watch for root spread near buildings.",
        "Yellow Flame": "Moderate watering needs. Prune to prevent branch breakage. Excellent urban tolerance.",
        "Sea Apple": "High water requirements. Minimal pruning needed. Native species - very low maintenance.",
        "Tembusu": "Drought tolerant - water only during extended dry periods. Light annual pruning. Excellent for urban environments.",
    }

    return care_guide.get(
        species_name,
        f"Care instructions for {species_name} are not available in our database. Please consult with a local arborist for specific guidance.",
    )


if __name__ == "__main__":
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8080),
        )
    )
