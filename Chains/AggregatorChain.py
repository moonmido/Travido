import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.AggregatedTravelState import AggregatedTravelState
from Instructions.AggregatorPrompt import Sys_Prompt
from langchain_core.prompts import ChatPromptTemplate

llm = config.chat_model(model=config.CHAIN_MODEL)
structuredLLM= llm.with_structured_output(AggregatedTravelState)

aggregatorPrompt = ChatPromptTemplate.from_messages([
    ("system", Sys_Prompt),
    ("human", "{user_query}"),
])

def aggregatorChain(user_query:str):
    """merge flight, hotel and destination research data"""

    return aggregatorPrompt | structuredLLM
