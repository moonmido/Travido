from States.DestinationState import DestinationState
from Instructions.DestinationResearchPrompt import Sys_Prompt
from langchain.agents import create_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from Tools.WebSearchTool import web_search
import os , config

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)
llm = ChatNVIDIA(model="openai/gpt-oss-20b",temperature=0,max_completion_tokens=1024)


def DestinationResearchAgent():
    """Create a Destination Research agent"""


    return create_agent(
        name="Destination Research Agent",
        system_prompt=Sys_Prompt,
        tools=[web_search],
        response_format=DestinationState,
    )
