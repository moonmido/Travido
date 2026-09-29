import os
import ssl
from typing import Optional

import certifi
from dotenv import load_dotenv

load_dotenv()

# The interpreter's default CA file is missing on this machine, so every
# TLS client (aiohttp in the NVIDIA SDK, httpx, requests) fails certificate
# verification. Point OpenSSL at the certifi bundle shipped in the venv.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

# The environment variable above is only read when an SSL context is CREATED,
# which for aiohttp (used by the NVIDIA SDK) can be cached before this module
# runs in some processes. Force the bundle into every default context instead,
# so the guarantee does not depend on import order.
_ssl_create_default_context = ssl.create_default_context


def _certifi_context(*args, **kwargs):
    context = _ssl_create_default_context(*args, **kwargs)
    try:
        context.load_verify_locations(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - never break TLS setup because of this
        pass
    return context


ssl.create_default_context = _certifi_context

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# The groq SDK appends /openai/v1 to the base URL itself.
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com")

# One Groq model for the whole workflow: gpt-oss-20b handles both the agents'
# forced tool calls and the chains' structured outputs.
AGENT_MODEL = os.getenv("TRAVIDO_AGENT_MODEL", "openai/gpt-oss-20b")
CHAIN_MODEL = os.getenv("TRAVIDO_CHAIN_MODEL", "openai/gpt-oss-20b")

# 1024 truncated the larger structured outputs (aggregator, package optimizer).
MAX_COMPLETION_TOKENS = int(os.getenv("TRAVIDO_MAX_COMPLETION_TOKENS", "4096"))

LLM_TIMEOUT = float(os.getenv("TRAVIDO_LLM_TIMEOUT", "300"))


def chat_model(model: Optional[str] = None, temperature: float = 0.0):
    """Build the Groq chat model shared by agents and chains."""

    from langchain_groq import ChatGroq

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set in .env - add your key from "
            "https://console.groq.com/keys"
        )

    return ChatGroq(
        model=model or AGENT_MODEL,
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        temperature=temperature,
        max_tokens=MAX_COMPLETION_TOKENS,
        timeout=LLM_TIMEOUT,
    )
