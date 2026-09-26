import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

import config

load_dotenv()
os.environ.setdefault("TAVILY_API_KEY", config.TAVILY_API_KEY)

_search = TavilySearch(
    max_results=8,
    topic="general",
    search_depth="advanced",
    include_answer=True,
    # raw page dumps grew the agent prompt to 350k+ chars and blew the context
    include_raw_content=False,
    include_images=False,
)


def get_web_search_tool() -> TavilySearch:
    return _search


@tool
def web_search(query: str) -> str:
    """Search the web for travel information such as flights, hotels, prices,
    attractions, restaurants, local transport and destination facts.

    Args:
        query: The search query.
    """

    return _search.invoke({"query": query})
