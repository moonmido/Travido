import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.DestinationState import DestinationState
from Instructions.DestinationResearchPrompt import Sys_Prompt
from langchain.agents import create_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from Tools.WebSearchTool import web_search
import os , config

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)
llm = ChatNVIDIA(model=config.AGENT_MODEL,temperature=0,max_completion_tokens=config.MAX_COMPLETION_TOKENS,timeout=config.LLM_TIMEOUT)


def DestinationResearchAgent():
    """Create a Destination Research agent"""


    return create_agent(
        model=llm,
        name="Destination Research Agent",
        system_prompt=Sys_Prompt,
        tools=[web_search],
        response_format=DestinationState,
    )
