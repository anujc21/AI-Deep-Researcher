from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable
from agents.research_agent import get_research_tool
from agents.drafting_agent import get_drafting_llm, draft_answer

class ResearchState:
    def __init__(self, query, research_output=None, final_answer=None):
        self.query = query
        self.research_output = research_output
        self.final_answer = final_answer

def research_node(state: ResearchState) -> ResearchState:
    research_tool = get_research_tool()
    result = research_tool.run(state.query)
    return ResearchState(query=state.query, research_output=result)

def draft_node(state: ResearchState) -> ResearchState:
    llm = get_drafting_llm()
    answer = draft_answer(llm, state.research_output)
    return ResearchState(query=state.query, research_output=state.research_output, final_answer=answer)

def create_workflow() -> Runnable:
    graph = StateGraph(ResearchState)
    graph.add_node("research", research_node)
    graph.add_node("draft", draft_node)
    
    graph.set_entry_point("research")
    graph.add_edge("research", "draft")
    graph.set_finish_point("draft")

    return graph.compile()
