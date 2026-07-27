from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
import os

def get_drafting_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.5,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

def draft_answer(llm, research_output, include_citations=True):
    """
    Draft an answer based on research output using the provided LLM.
    
    Args:
        llm: The language model to use
        research_output: The research results to summarize
        include_citations: Whether to include citations in the summary
    
    Returns:
        The drafted answer as a string
    """
    instructions = "You are an expert analyst. Draft a well-organized summary from the following information."
    
    if include_citations:
        instructions += " Include relevant citations where appropriate."
    else:
        instructions += " Focus on presenting the information without citations."
    
    messages = [
        SystemMessage(content=instructions),
        HumanMessage(content=research_output)
    ]
    
    return llm(messages).content