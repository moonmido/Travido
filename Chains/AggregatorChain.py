import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from States.AggregatedTravelState import AggregatedTravelState
from Instructions.AggregatorPrompt import Sys_Prompt
from langchain_core.prompts import ChatPromptTemplate
import config , os

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)

llm = ChatNVIDIA(model=config.CHAIN_MODEL,temperature=0,max_completion_tokens=config.MAX_COMPLETION_TOKENS,timeout=config.LLM_TIMEOUT)
structuredLLM= llm.with_structured_output(AggregatedTravelState)

aggregatorPrompt = ChatPromptTemplate.from_messages([
    ("system", Sys_Prompt),
    ("human", "{user_query}"),
])

def aggregatorChain(user_query:str):
    """merge flight, hotel and destination research data"""

    return aggregatorPrompt | structuredLLM
