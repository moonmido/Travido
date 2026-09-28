import os
import ssl

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

# Two models are needed, neither one works for both jobs:
#
#   AGENT_MODEL  honours tool_choice="required", so create_agent(..., response_format=...)
#                returns a real structured response. gpt-oss-20b silently ignored the
#                forced tool call and answered in prose, which produced empty state.
#   CHAIN_MODEL   is much faster on with_structured_output. The agent model needs
#                ~90s+ per large response_format call, which the default SDK read
#                timeout cuts off.
AGENT_MODEL = os.getenv("TRAVIDO_AGENT_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
CHAIN_MODEL = os.getenv("TRAVIDO_CHAIN_MODEL", "openai/gpt-oss-20b")

# 1024 truncated the larger structured outputs (aggregator, package optimizer).
MAX_COMPLETION_TOKENS = int(os.getenv("TRAVIDO_MAX_COMPLETION_TOKENS", "4096"))

# ChatNVIDIA's default read timeout aborts slow model calls, which surfaces as a
# retryable SocketTimeoutError rather than a real failure.
LLM_TIMEOUT = float(os.getenv("TRAVIDO_LLM_TIMEOUT", "300"))
