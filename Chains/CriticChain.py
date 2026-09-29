import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.CriticState import CriticState
from Instructions.CriticPrompt import Sys_Prompt
from langchain_core.prompts import ChatPromptTemplate

llm = config.chat_model(model=config.CHAIN_MODEL)
structuredLLM= llm.with_structured_output(CriticState)

criticPrompt = ChatPromptTemplate.from_messages([
    ("system", Sys_Prompt),
    ("human", "{user_query}"),
])

def criticChain(user_query:str):
    """build the Critic based on query"""

    return criticPrompt | structuredLLM

