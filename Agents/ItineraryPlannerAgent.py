import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.ItineraryState import ItineraryState
from Instructions.ItineraryPlannerPrompt import Sys_Prompt
from langchain.agents import create_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from Tools.WeatherApi import get_current_weather,get_weather_forecast
from Tools.WebSearchTool import web_search
from Tools.RoutesApi import calculate_route
import os , config

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)
llm = ChatNVIDIA(model=config.AGENT_MODEL,temperature=0,max_completion_tokens=config.MAX_COMPLETION_TOKENS,timeout=config.LLM_TIMEOUT)


def ItineraryPlannerAgent():
    """Create a Itinerary Planner agent"""


    return create_agent(
        model=llm,
        name="Itinerary Planner Agent",
        system_prompt=Sys_Prompt,
        tools=[get_weather_forecast,get_current_weather,calculate_route,web_search],
        response_format=ItineraryState,
    )
