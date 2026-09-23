from langchain_nvidia_ai_endpoints import ChatNVIDIA
from States.ConstraintBuilderState import ConstraintBuilderState
from Instructions.ConstraintBuilderPrompt import Sys_Prompt
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate , HumanMessagePromptTemplate
import config , os

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)

llm = ChatNVIDIA(model="openai/gpt-oss-20b",temperature=0,max_completion_tokens=1024)
structuredLLM= llm.with_structured_output(ConstraintBuilderState)

def constraintChain(query:str):
    """build the constraint based on user query"""

    constraintPrompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate(Sys_Prompt),
        (HumanMessagePromptTemplate(query))
    ])

    return constraintPrompt | structuredLLM







