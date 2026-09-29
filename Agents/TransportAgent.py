import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.TransportState import TransportState
from Instructions.TransportPrompt import Sys_Prompt
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from Tools.WebSearchTool import web_search
from Tools.RoutesApi import calculate_route

llm = config.chat_model(model=config.AGENT_MODEL)


def TransportAgent():
    """Create a Transport agent"""


    return create_agent(
        model=llm,
        name="Transport Agent",
        system_prompt=Sys_Prompt,
        tools=[web_search,calculate_route],
        response_format=ToolStrategy(schema=TransportState),
    )
