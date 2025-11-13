import os
import logging
import google.cloud.logging
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.langchain_tool import LangchainTool

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

import google.auth
import google.auth.transport.requests
import google.oauth2.id_token

# --- Setup Logging and Environment ---
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

load_dotenv()

model_name = os.getenv("MODEL")


# Greet user and save their prompt
def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logging.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}

def get_id_token():
    """Get an ID token to authenticate with the MCP server."""
    target_url = os.getenv("MCP_SERVER_URL")
    audience = target_url.split('/mcp/')[0]
    request = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(request, audience)
    return id_token

# Configuring the MCP Tool to connect to the Tree Planting Agent MCP server
mcp_server_url = os.getenv("MCP_SERVER_URL")
if not mcp_server_url:
    raise ValueError("The environment variable MCP_SERVER_URL is not set.")

mcp_tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=mcp_server_url,
        headers={
            "Authorization": f"Bearer {get_id_token()}",
        },
        timeout=300,  # 5 minutes timeout for long-running analysis
    ),
)

# Configuring the Wikipedia Tool
wikipedia_tool = LangchainTool(
    tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
)

# 1. Researcher Agent
comprehensive_researcher = Agent(
    name="comprehensive_researcher",
    model=model_name,
    description="The primary researcher that can access both internal data about tree planting analysis in Kuala Lumpur or Selangor, Malaysia and external knowledge from Wikipedia.",
    instruction="""
    You are a helpful research assistant for tree planting recommendations. Your goal is to fully answer the user's PROMPT.
    
    You have access to three MCP tools and one Wikipedia tool:
    1. search_all_matching_location_based_on_keyword - Find locations by keyword/address
    2. analyze_tree_planting_opportunities - Analyze a specific location for tree planting
    3. get_tree_species_recommendations - Get suitable tree species for the area
    4. Wikipedia - Search for general tree knowledge (species info, benefits, care)

    WORKFLOW - Follow this sequence for location-based queries:
    
    STEP 1: LOCATION SEARCH
    - If user provides a location query (building, landmark, area in KL/Selangor):
      → Use 'search_all_matching_location_based_on_keyword' with the location keyword
      → If NO results found: inform user location not available
      → If MULTIPLE results: confirm with user which location is correct (show options)
      → If ONE result: proceed to Step 2
    
    STEP 2: ANALYZE LOCATION
    - Once you have the correct location (latitude, longitude, name):
      → Use 'analyze_tree_planting_opportunities' with the lat/lon/name
      → This will return analysis results including:
        * Satellite imagery analysis
        * Detected vegetation coverage
        * Shadow patterns
        * Priority scores for planting zones
        * Visualization file paths
      → Store this analysis data for the response
    
    STEP 3: GET TREE RECOMMENDATIONS
    - After analyzing the location:
      → Use 'get_tree_species_recommendations' to get suitable tree species
      → This returns species suitable for Kuala Lumpur climate
      → Include species characteristics, growth requirements, benefits
    
    STEP 4: ENRICH WITH WIKIPEDIA (Optional)
    - If user asks about specific tree species or general tree information:
      → Use Wikipedia to get additional facts (habitat, lifespan, ecology)
      → Supplement the MCP recommendations with general knowledge
    
    IMPORTANT NOTES:
    - Always follow the sequence: Search → Analyze → Recommendations
    - Pass the exact latitude, longitude, and location name from search results to analyze tool
    - The analyze tool generates visualization files - mention these in your output
    - Synthesize all tool results into comprehensive preliminary data
    - If analysis fails or errors, report the issue to the user
    
    PROMPT:
    {{ PROMPT }}
    """,
    tools=[mcp_tools, wikipedia_tool],
    output_key="research_data",  # A key to store the combined findings
)

# 2. Response Formatter Agent
response_formatter = Agent(
    name="response_formatter",
    model=model_name,
    description="Synthesizes all information into a friendly, readable response.",
    instruction="""
    You are the friendly voice of the Tree Planting Guide. Your task is to take the
    RESEARCH_DATA and present it to the user in a complete and helpful answer.

    - First, present the specific information from the tree planting data (like species, 
    locations, and care instructions) in the location user provided.
    - Then, add the interesting general facts from the research.
    - CRITICAL: If the research data contains 'visualization_urls', you MUST embed the analysis map using HTML.
      Format it exactly like this:
      
      "📊 **Detailed Analysis Visualization**
      
      <img src='[analysis_map_url]' style='max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;' alt='Tree Planting Analysis Map'/>
      
      This 6-panel visualization shows:
      1. Original satellite imagery
      2. Detected vegetation (NDVI analysis)
      3. Shadow patterns (sun exposure)
      4. Street network and building footprints
      5. Priority scores (color-coded zones)
      6. Final recommended planting locations
      "
      
    - Replace [analysis_map_url] with the actual URL from visualization_urls['analysis_map']
    - Do NOT show the component breakdown image - it's stored for reference only
    - Always use <img> tags with the exact style attribute shown above
    - If some information is missing, just present the information you have.
    - Be conversational and engaging.

    RESEARCH_DATA:
    {{ research_data }}
    """,
)

# The Workflow Agent
tree_planting_guide_workflow = SequentialAgent(
    name="tree_planting_guide_workflow",
    description="The main workflow for handling a user's request about tree planting advice near Kuala Lumpur or Selangor, Malaysia,.",
    sub_agents=[
        comprehensive_researcher,  # Step 1: Gather all data
        response_formatter,  # Step 2: Format the final response
    ],
)


# Main Root Agent
root_agent = Agent(
    name="greeter",
    model=model_name,
    description="The main entry point for the Tree Planting Guide.",
    instruction="""
    - You are the Tree Planting Guide for the areas in Kuala Lumpur or Selangor, Malaysia. Always start by greeting the user warmly and explaining that you can help them with tree planting advice if user provides a location such as building name.
    - When the user responds, use the 'add_prompt_to_state' tool to save their response.
    - After using the tool, transfer control to the 'tree_planting_guide_workflow' agent.
    """,
    tools=[add_prompt_to_state],
    sub_agents=[tree_planting_guide_workflow],
)
