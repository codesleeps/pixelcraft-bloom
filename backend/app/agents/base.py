"""Base agent utilities and classes for AgentScope integration.

This module provides the foundation for building AI agents with memory,
tools, and logging capabilities. It includes classes for agent configuration,
memory management, tool definitions, and response handling.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
import json
import logging
import time
from supabase import Client, create_client
import os
from dotenv import load_dotenv
from ..models.manager import ModelManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
try:
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_KEY", "")
    )
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None


@dataclass
class AgentMessage:
    """Class representing a message in the agent's memory."""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemory:
    """Class representing an agent's memory storage."""
    conversation_id: str
    messages: List[AgentMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a new message to the memory."""
        self.messages.append(AgentMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        ))

    def get_recent_messages(self, limit: int = 10) -> List[AgentMessage]:
        """Get the most recent messages from memory."""
        return self.messages[-limit:]

    def get_context_string(self, limit: int = 5) -> str:
        """Get a formatted string of recent messages for context."""
        recent = self.get_recent_messages(limit)
        context = []
        for msg in recent:
            context.append(f"{msg.role.upper()}: {msg.content}")
        return "\n".join(context)


@dataclass
class AgentTool:
    """Class representing a tool available to the agent."""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    required_params: List[str] = field(default_factory=list)

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate that all required parameters are present."""
        return all(param in params for param in self.required_params)


@dataclass
class BaseAgentConfig:
    """Configuration class for BaseAgent."""
    agent_id: str
    name: str
    description: str
    default_model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: str = ""
    capabilities: List[str] = field(default_factory=list)
    tools: List[AgentTool] = field(default_factory=list)
    task_type: str = "general"
    model_manager: Optional[ModelManager] = None


@dataclass
class AgentResponse:
    """Class representing an agent's response."""
    content: str
    agent_id: str
    conversation_id: str
    metadata: Dict[str, Any]
    tools_used: List[str]
    model_used: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary format."""
        return {
            "content": self.content,
            "agent_id": self.agent_id,
            "conversation_id": self.conversation_id,
            "metadata": self.metadata,
            "tools_used": self.tools_used,
            "model_used": self.model_used,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent:
    """Base class for all agents in the system."""

    def __init__(self, config: BaseAgentConfig):
        self.config = config
        self.memory_store: Dict[str, AgentMemory] = {}
        self.tools: Dict[str, AgentTool] = {tool.name: tool for tool in config.tools}
        self.model_manager = config.model_manager
        self.logger = logging.getLogger(f"agent.{config.agent_id}")

    async def set_shared_memory(self, conversation_id: str, key: str, value: Any, scope: str = 'conversation', workflow_execution_id: Optional[str] = None, expires_at: Optional[datetime] = None) -> None:
        """Set a shared memory entry for the given conversation and key."""
        if not supabase:
            self.logger.warning("Supabase client not available, cannot set shared memory")
            return
        try:
            # Serialize value to JSON-compatible format
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                memory_value = value
            else:
                memory_value = str(value)
            memory_entry = {
                "conversation_id": conversation_id,
                "workflow_execution_id": workflow_execution_id,
                "memory_key": key,
                "memory_value": memory_value,
                "scope": scope,
                "created_by_agent": self.config.agent_id,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("shared_memory").upsert(memory_entry, on_conflict="conversation_id,memory_key,scope").execute()
            self.logger.debug(f"Set shared memory for key '{key}' in conversation '{conversation_id}'")
        except Exception as e:
            self.logger.warning(f"Failed to set shared memory: {e}")

    async def get_shared_memory(self, conversation_id: str, key: str, scope: str = 'conversation', workflow_execution_id: Optional[str] = None) -> Optional[Any]:
        """Retrieve a shared memory entry for the given conversation and key."""
        if not supabase:
            return None
        try:
            query = supabase.table("shared_memory").select("memory_value,access_count,expires_at").eq("conversation_id", conversation_id).eq("memory_key", key).eq("scope", scope)
            if workflow_execution_id:
                query = query.eq("workflow_execution_id", workflow_execution_id)
            result = query.execute()
            if not result.data:
                return None
            data = result.data[0]
            # Check if expired
            if data.get("expires_at"):
                expires_at = datetime.fromisoformat(data["expires_at"])
                if datetime.utcnow() > expires_at:
                    return None
            # Increment access count
            access_count = data.get("access_count", 0)
            supabase.table("shared_memory").update({"access_count": access_count + 1}).eq("conversation_id", conversation_id).eq("memory_key", key).eq("scope", scope).execute()
            return data["memory_value"]
        except Exception as e:
            self.logger.warning(f"Failed to get shared memory: {e}")
            return None

    async def list_shared_memory_keys(self, conversation_id: str, scope: str = 'conversation', workflow_execution_id: Optional[str] = None) -> List[str]:
        """List all shared memory keys for the given conversation and scope."""
        if not supabase:
            return []
        try:
            query = supabase.table("shared_memory").select("memory_key").eq("conversation_id", conversation_id).eq("scope", scope)
            if workflow_execution_id:
                query = query.eq("workflow_execution_id", workflow_execution_id)
            result = query.execute()
            return [row["memory_key"] for row in result.data]
        except Exception as e:
            self.logger.warning(f"Failed to list shared memory keys: {e}")
            return []

    async def delete_shared_memory(self, conversation_id: str, key: str, scope: str = 'conversation') -> None:
        """Delete a shared memory entry for the given conversation and key."""
        if not supabase:
            return
        try:
            supabase.table("shared_memory").delete().eq("conversation_id", conversation_id).eq("memory_key", key).eq("scope", scope).execute()
            self.logger.debug(f"Deleted shared memory for key '{key}' in conversation '{conversation_id}'")
        except Exception as e:
            self.logger.warning(f"Failed to delete shared memory: {e}")

    def get_memory(self, conversation_id: str) -> AgentMemory:
        """Get or create memory for a conversation."""
        if conversation_id not in self.memory_store:
            self.memory_store[conversation_id] = AgentMemory(conversation_id=conversation_id)
        return self.memory_store[conversation_id]

    def clear_memory(self, conversation_id: str) -> None:
        """Clear memory for a specific conversation."""
        if conversation_id in self.memory_store:
            del self.memory_store[conversation_id]

    async def use_tool(self, conversation_id: str, tool_name: str, params: Dict[str, Any]) -> Any:
        """Use a specific tool with given parameters."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]
        if not tool.validate_params(params):
            raise ValueError(f"Missing required parameters for tool '{tool_name}'")

        start_time = time.time()
        try:
            result = await tool.function(**params)
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._log_tool_execution(conversation_id, tool_name, params, result, execution_time_ms)
            return result
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._log_tool_execution(conversation_id, tool_name, params, None, execution_time_ms, str(e))
            self.logger.error(f"Error using tool '{tool_name}': {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build the complete system prompt including capabilities and tools."""
        prompt_parts = [self.config.system_prompt]

        if self.config.capabilities:
            prompt_parts.append("\nCapabilities:")
            for cap in self.config.capabilities:
                prompt_parts.append(f"- {cap}")

        if self.tools:
            prompt_parts.append("\nAvailable Tools:")
            for tool in self.tools.values():
                prompt_parts.append(f"- {tool.name}: {tool.description}")
                if tool.required_params:
                    prompt_parts.append(f"  Required parameters: {', '.join(tool.required_params)}")

        prompt_parts.append("\nModel Optimization: Leverage the selected AI model's capabilities for optimal performance.")

        return "\n".join(prompt_parts)

    async def _log_interaction(self, 
                             conversation_id: str,
                             action: str,
                             input_data: Dict[str, Any],
                             output_data: Dict[str, Any],
                             error_message: Optional[str] = None) -> None:
        """Log an interaction to the Supabase agent_logs table."""
        if not supabase:
            self.logger.warning("Supabase client not initialized, skipping log")
            return

        try:
            log_entry = {
                "agent_type": self.config.agent_id,
                "conversation_id": conversation_id,
                "action": action,
                "input_data": input_data,
                "output_data": output_data,
                "status": "error" if error_message else "success",
                "error_message": error_message,
                "created_at": datetime.utcnow().isoformat()
            }

            supabase.table("agent_logs").insert(log_entry).execute()
        except Exception as e:
            self.logger.error(f"Failed to log interaction: {e}")

    async def _log_tool_execution(self, conversation_id: str, tool_name: str, params: Dict[str, Any], result: Any, execution_time_ms: int, error_message: Optional[str] = None) -> None:
        """Log tool execution to the Supabase agent_logs table."""
        if not supabase:
            self.logger.warning("Supabase client not initialized, skipping tool execution log")
            return

        try:
            # Handle non-serializable result by converting to string
            serializable_result = result
            if not isinstance(result, (dict, list, str, int, float, bool, type(None))):
                serializable_result = str(result)
            
            log_entry = {
                "agent_type": self.config.agent_id,
                "conversation_id": conversation_id,
                "action": f"tool_execution:{tool_name}",
                "input_data": {"tool_name": tool_name, "parameters": params},
                "output_data": {"result": serializable_result},
                "execution_time_ms": execution_time_ms,
                "status": "error" if error_message else "success",
                "error_message": error_message,
                "created_at": datetime.utcnow().isoformat()
            }

            supabase.table("agent_logs").insert(log_entry).execute()
        except Exception as e:
            self.logger.warning(f"Failed to log tool execution: {e}")

    async def _generate_with_model(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate response using ModelManager with automatic model selection and fallback."""
        return await self.model_manager.generate(prompt, self.config.task_type, system_prompt, **kwargs)

    async def _chat_with_model(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using ModelManager with automatic model selection and fallback."""
        response = await self.model_manager.chat(messages, self.config.task_type, **kwargs)
        return response["message"]["content"]

    async def process_message(self, conversation_id: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process a message and return a response. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement process_message method")
