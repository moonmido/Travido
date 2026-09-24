from States.TransportState import TransportState
from Instructions.TransportPrompt import Sys_Prompt
from langchain.agents import create_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from Tools.WebSearchTool import web_search
from Tools.RoutesApi import calculate_route
import os , config

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)
llm = ChatNVIDIA(model="openai/gpt-oss-20b",temperature=0,max_completion_tokens=1024)


def TransportAgent():
    """Create a Transport agent"""


    return create_agent(
        name="Transport Agent",
        system_prompt=Sys_Prompt,
        tools=[web_search,calculate_route],
        response_format=TransportState,
    )
