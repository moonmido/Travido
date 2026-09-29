import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.ItineraryState import ItineraryState
from Instructions.ItineraryPlannerPrompt import Sys_Prompt
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from Tools.WeatherApi import get_current_weather,get_weather_forecast
from Tools.WebSearchTool import web_search
from Tools.RoutesApi import calculate_route

llm = config.chat_model(model=config.AGENT_MODEL)


def ItineraryPlannerAgent():
    """Create a Itinerary Planner agent"""


    return create_agent(
        model=llm,
        name="Itinerary Planner Agent",
        system_prompt=Sys_Prompt,
        tools=[get_weather_forecast,get_current_weather,calculate_route,web_search],
        response_format=ToolStrategy(schema=ItineraryState),
    )
