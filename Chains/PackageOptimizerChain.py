import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.PackageState import PackageState
from Instructions.PackageOptimizerPrompt import Sys_Prompt
from langchain_core.prompts import ChatPromptTemplate

llm = config.chat_model(model=config.CHAIN_MODEL)
structuredLLM= llm.with_structured_output(PackageState)

packageOptimizerPrompt = ChatPromptTemplate.from_messages([
    ("system", Sys_Prompt),
    ("human", "{user_query}"),
])

def packageOptimizerChain(user_query:str):
    """build the package optimizer based on query"""

    return packageOptimizerPrompt | structuredLLM


