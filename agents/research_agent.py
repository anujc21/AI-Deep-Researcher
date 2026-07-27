from langchain.agents import tool
from langchain.tools.tavily_search import TavilySearchResults

@tool
def web_research_tool(query: str) -> str:
    """Research the web for current information based on a query."""
    search_tool = TavilySearchResults()
    results = search_tool.run(query)
    return results
