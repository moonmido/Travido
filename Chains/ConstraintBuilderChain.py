import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
from States.ConstraintBuilderState import ConstraintBuilderState
from Instructions.ConstraintBuilderPrompt import Sys_Prompt
from langchain_core.prompts import ChatPromptTemplate

llm = config.chat_model(model=config.CHAIN_MODEL)
structuredLLM= llm.with_structured_output(ConstraintBuilderState)

constraintPrompt = ChatPromptTemplate.from_messages([
    ("system", Sys_Prompt),
    ("human", "{user_query}"),
])

def constraintChain(user_query:str):
    """build the constraint based on user query"""

    return constraintPrompt | structuredLLM







