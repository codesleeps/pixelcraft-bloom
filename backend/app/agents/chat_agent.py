from typing import Any, Dict, Optional
from .base import BaseAgent, BaseAgentConfig
from ..utils.ollama_client import get_ollama_client
from ..utils.supabase_client import get_supabase_client
import logging

logger = logging.getLogger("pixelcraft.agents.chat")


class ChatAgent(BaseAgent):
    def __init__(self, cfg: BaseAgentConfig):
        super().__init__(cfg)
        self.model = None

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the chat agent. Expects input_data to contain 'message' and optional metadata."""
        message = input_data.get("message") or input_data.get("text") or ""
        conversation_id = input_data.get("conversation_id")
        user_id = input_data.get("user_id")

        # try to use Ollama model via AgentScope binding
        try:
            model = get_ollama_client()
            # AgentScope's OllamaChatModel may have a `chat` or `generate` method
            if hasattr(model, "chat"):
                resp = model.chat([{"role": "user", "content": message}])
                # resp may be a dict or object
                text = resp.get("response") if isinstance(resp, dict) else str(resp)
            elif hasattr(model, "generate"):
                gen = model.generate(message)
                text = getattr(gen, "text", str(gen))
            else:
                text = f"Echo: {message}"
        except Exception as exc:
            logger.exception("ChatAgent failed to call Ollama: %s", exc)
            text = f"Echo: {message}"

        # Persist message and agent response to Supabase conversations table if available
        try:
            sb = get_supabase_client()
            sb.table("conversations").insert({
                "conversation_id": conversation_id or "",
                "role": "user",
                "content": message,
            }).execute()
            sb.table("conversations").insert({
                "conversation_id": conversation_id or "",
                "role": "assistant",
                "content": text,
            }).execute()
        except Exception:
            # ignore persistence errors in agent
            pass

        return {"response": text, "conversation_id": conversation_id or ""}
