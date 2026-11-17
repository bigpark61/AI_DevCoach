import os

from openai import OpenAI


def create_ai_client() -> OpenAI | None:
    gateway_token = os.getenv("NEON_AI_GATEWAY_TOKEN", "").strip()
    gateway_base_url = os.getenv("NEON_AI_GATEWAY_BASE_URL", "").strip().rstrip("/")
    if gateway_token and gateway_base_url:
        return OpenAI(
            api_key=gateway_token,
            base_url=f"{gateway_base_url}/v1",
            timeout=30.0,
            max_retries=1,
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    options: dict[str, object] = {
        "api_key": api_key,
        "timeout": 30.0,
        "max_retries": 1,
    }
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if base_url:
        options["base_url"] = base_url
    return OpenAI(**options)


def configured_model() -> str:
    return (
        os.getenv("AI_MODEL", "").strip()
        or os.getenv("OPENAI_MODEL", "").strip()
        or "gpt-4o-mini"
    )
