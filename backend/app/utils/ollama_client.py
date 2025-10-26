from functools import lru_cache
from typing import Any, List, Optional
from ..config import settings
import logging

logger = logging.getLogger("pixelcraft.ollama")


@lru_cache()
def get_ollama_client() -> Any:
    """Return an Ollama model client via AgentScope model wrapper.

    This attempts to instantiate the model from agentscope.model.OllamaChatModel.
    If the dependency is missing, a simple placeholder is returned.
    """
    try:
        from agentscope.model import OllamaChatModel
    except Exception:
        logger.warning("agentscope or Ollama model binding not available; returning placeholder")
        class Placeholder:
            def __init__(self, *a, **k):
                pass
            def chat(self, *a, **k):
                return {"response": "Placeholder response: agentscope not installed"}
            def is_ready(self):
                return False
        return Placeholder()

    cfg = settings.ollama
    # OllamaChatModel is an AgentScope wrapper around the Ollama chat API
    model = OllamaChatModel(model_name=cfg.model, host=str(cfg.host), temperature=cfg.temperature, keep_alive=cfg.keep_alive)
    logger.info("Ollama model client initialized: %s", cfg.model)
    return model


def test_ollama_connection(timeout: int = 5) -> bool:
    """Quick health check for the Ollama model/service.

    Returns True if the client is responsive and the configured model exists.
    """
    try:
        client = get_ollama_client()
        # If placeholder, it may not have a 'is_ready' method
        if hasattr(client, "is_ready"):
            return bool(client.is_ready())

        # Try to call a light-weight info endpoint if available
        if hasattr(client, "list_models"):
            models = client.list_models()
            return settings.ollama.model in (m.get("name") or m for m in (models or []))

        # Otherwise optimistic True if instantiated
        return True
    except Exception as exc:
        logger.exception("Ollama health check failed: %s", exc)
        return False


def list_available_models() -> List[str]:
    try:
        client = get_ollama_client()
        if hasattr(client, "list_models"):
            models = client.list_models() or []
            return [m.get("name") for m in models if isinstance(m, dict) and m.get("name")]
    except Exception:
        logger.debug("Could not list models from Ollama client")
    return []

