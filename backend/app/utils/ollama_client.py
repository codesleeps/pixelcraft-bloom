import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import aiohttp

from ..config import settings

logger = logging.getLogger("agentsflowai.ollama")


class OllamaClient:
    """Direct Ollama API client using aiohttp for async operations."""

    def __init__(self, host: str, timeout: float = 30.0, keep_alive: str = "10m"):
        self.host = host.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.keep_alive = keep_alive
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(timeout=self.timeout, connector=aiohttp.TCPConnector(limit=10))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout, connector=aiohttp.TCPConnector(limit=10))

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        await self._ensure_session()
        url = f"{self.host}{endpoint}"
        try:
            logger.debug("Ollama request %s %s payload=%s", "POST", url, {k: v for k, v in data.items() if k != "prompt"})
            async with self._session.post(url, json=data) as resp:
                # If server returned an error status, capture body for debugging
                if resp.status >= 400:
                    try:
                        body = await resp.text()
                    except Exception:
                        body = "<unable to read response body>"
                    logger.error("Ollama API %s returned status %s body=%s", endpoint, resp.status, body)
                    resp.raise_for_status()

                if data.get("stream", True):
                    # Handle streaming response
                    full_response = {}
                    async for line in resp.content:
                        try:
                            line = line.strip()
                            if not line:
                                continue
                            chunk = json.loads(line.decode("utf-8"))
                        except Exception as parse_exc:
                            logger.warning("Failed to parse stream chunk from Ollama: %s", parse_exc)
                            continue
                        if chunk.get("done"):
                            full_response.update(chunk)
                            break
                        else:
                            # Accumulate content
                            if "message" in chunk:
                                if "message" not in full_response:
                                    full_response["message"] = {"content": ""}
                                full_response["message"]["content"] += chunk["message"].get("content", "")
                            elif "response" in chunk:
                                if "response" not in full_response:
                                    full_response["response"] = ""
                                full_response["response"] += chunk.get("response", "")
                    return full_response
                else:
                    try:
                        return await resp.json()
                    except Exception as json_exc:
                        text = await resp.text()
                        logger.error("Failed to decode JSON response from Ollama: %s; raw=%s", json_exc, text)
                        raise
        except Exception as e:
            logger.exception("Error calling Ollama API %s", endpoint)
            raise

    async def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Perform a chat completion using Ollama /api/chat."""
        data = {
            "model": model,
            "messages": messages,
            "stream": kwargs.get("stream", settings.ollama.stream),
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": kwargs.get("temperature", settings.ollama.temperature),
                "num_predict": kwargs.get("max_tokens", 1000),
            }
        }
        data["options"].update(kwargs.get("options", {}))
        response = await self._post("/api/chat", data)
        # Ensure response has "message" with "content"
        if "message" not in response:
            response["message"] = {"content": response.get("response", "")}
        return response

    async def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Perform text generation using Ollama /api/generate."""
        data = {
            "model": model,
            "prompt": prompt,
            "stream": kwargs.get("stream", settings.ollama.stream),
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": kwargs.get("temperature", settings.ollama.temperature),
                "num_predict": kwargs.get("max_tokens", 1000),
            }
        }
        data["options"].update(kwargs.get("options", {}))
        response = await self._post("/api/generate", data)
        # Wrap in "message" format for consistency with agents
        if "response" in response:
            response["message"] = {"content": response.pop("response")}
        return response

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models via /api/tags."""
        await self._ensure_session()
        url = f"{self.host}/api/tags"
        try:
            async with self._session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("models", [])
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def is_ready(self, model: Optional[str] = None) -> bool:
        """Check if Ollama is ready and model is available."""
        try:
            models = await self.list_models()
            model_names = [m.get("name") for m in models]
            if model:
                return model in model_names
            return bool(model_names)
        except Exception:
            return False


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Return the global Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        cfg = settings.ollama
        _ollama_client = OllamaClient(
            host=str(cfg.host),
            timeout=600.0,  # Increase default timeout to 10 minutes to accommodate model loading/generation on constrained systems
            keep_alive=cfg.keep_alive
        )
    return _ollama_client


async def test_ollama_connection(timeout: int = 5) -> bool:
    """Async health check for the Ollama service."""
    client = get_ollama_client()
    try:
        # Temporarily adjust timeout for health check
        original_timeout = client.timeout
        client.timeout = aiohttp.ClientTimeout(total=timeout)
        ready = await client.is_ready(settings.ollama.model)
        client.timeout = original_timeout
        return ready
    except Exception as exc:
        logger.exception("Ollama health check failed: %s", exc)
        return False


async def list_available_models() -> List[str]:
    """Async list of available model names."""
    client = get_ollama_client()
    try:
        models = await client.list_models()
        return [m.get("name") for m in models if isinstance(m, dict) and m.get("name")]
    except Exception:
        logger.debug("Could not list models from Ollama client")
        return []

