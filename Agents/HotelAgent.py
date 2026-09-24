from States.HotelState import HotelState
from Instructions.HotelPrompt import Sys_Prompt
from langchain.agents import create_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_tavily import TavilySearch
import os , config

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)
llm = ChatNVIDIA(model="openai/gpt-oss-20b",temperature=0,max_completion_tokens=1024)

def HotelAgent():
    """Create a hotel agent"""

    search_tool = TavilySearch(
        max_results=8,
        topic="general",
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=False,
    )

    return create_agent(
        name="Hotel Agent",
        system_prompt=Sys_Prompt,
        tools=[search_tool],
        response_format=HotelState,
    )


