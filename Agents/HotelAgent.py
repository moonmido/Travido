import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.HotelState import HotelState
from Instructions.HotelPrompt import Sys_Prompt
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from Tools.WebSearchTool import web_search

llm = config.chat_model(model=config.AGENT_MODEL)

def HotelAgent():
    """Create a hotel agent"""

    return create_agent(
        model=llm,
        name="Hotel Agent",
        system_prompt=Sys_Prompt,
        tools=[web_search],
        response_format=ToolStrategy(schema=HotelState),
    )


