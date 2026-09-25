from langchain_nvidia_ai_endpoints import ChatNVIDIA
from States.CriticState import CriticState
from Instructions.CriticPrompt import Sys_Prompt
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate , HumanMessagePromptTemplate
import config , os

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)

llm = ChatNVIDIA(model="openai/gpt-oss-20b",temperature=0,max_completion_tokens=1024)
structuredLLM= llm.with_structured_output(CriticState)

def criticChain(query:str):
    """build the Critic based on query"""

    criticChain = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate(Sys_Prompt),
        (HumanMessagePromptTemplate(query))
    ])

    return criticChain | structuredLLM

