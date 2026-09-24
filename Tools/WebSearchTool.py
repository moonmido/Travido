from langchain_tavily import TavilySearch

def web_search():
   return TavilySearch(
        max_results=8,
        topic="general",
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=False,
    )
