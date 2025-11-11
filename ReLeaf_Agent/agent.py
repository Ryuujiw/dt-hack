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


# Configuring the MCP Tool to connect to the Tree Planting Agent MCP server
mcp_server_url = os.getenv("MCP_SERVER_URL")
if not mcp_server_url:
    raise ValueError("The environment variable MCP_SERVER_URL is not set.")


mcp_tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=mcp_server_url)
)

# Configuring the Wikipedia Tool
wikipedia_tool = LangchainTool(
    tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
)

# 1. Researcher Agent
comprehensive_researcher = Agent(
    name="comprehensive_researcher",
    model=model_name,
    description="The primary researcher that can access both internal data about existing planted trees in area of Kuala Lumpur or Selangor, Malaysia and external knowledge from Wikipedia.",
    instruction="""
    You are a helpful research assistant. Your goal is to fully answer the user's PROMPT.
    You have access to two tools:
    1. A tool for getting user prompt and find the address with its latitude and longitude, and getting specific data about existing planted trees in Kuala Lumpur or Selangor, Malaysia and the suggestions for
    the area where more trees can be planted in the area.
    2. A tool for searching Wikipedia for general knowledge (facts, lifespan, diet, habitat).

    First, analyze the user's PROMPT.
    - If user provides a location-related query about tree planting in Kuala Lumpur or Selangor, Malaysia, 
      first find the location using the MCP tool. If the location is not found, inform the user that no data 
      is available for that location. If there are more than one location found, confirm with user which
      location is the correct one. If there is only one location, proceed to get the data about existing 
      planted trees and suggestions for planting more trees in that area.
    - If the prompt can be answered by only one tool, use that tool.
    - If the prompt is complex and requires information from both the tree's database AND Wikipedia,
      you MUST use both tools to gather all necessary information.
    - Use the Gemini model's capabilities to reason through the steps needed to answer the prompt completely.
    - Synthesize the results from the tool(s) you use into preliminary data outputs.

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
