from langchain_nvidia_ai_endpoints import ChatNVIDIA
from States.PackageState import PackageState
from Instructions.PackageOptimizerPrompt import Sys_Prompt
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate , HumanMessagePromptTemplate
import config , os

os.environ.setdefault("NVIDIA_API_KEY", config.NVIDIA_API_KEY)

llm = ChatNVIDIA(model="openai/gpt-oss-20b",temperature=0,max_completion_tokens=1024)
structuredLLM= llm.with_structured_output(PackageState)

def constraintChain(query:str):
    """build the package optimizer based on query"""

    packageOptimizerPrompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate(Sys_Prompt),
        (HumanMessagePromptTemplate(query))
    ])

    return packageOptimizerPrompt | structuredLLM


