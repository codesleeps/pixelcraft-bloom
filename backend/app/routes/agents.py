from fastapi import APIRouter, HTTPException
from typing import List
import time

from ..models.agent import AgentListResponse, AgentInfo, AgentRequest, AgentResponse
from ..config import settings
from ..agents.orchestrator import orchestrator

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents():
    agents = []
    for agent_id, agent in orchestrator.registry.items():
        info = AgentInfo(agent_id=agent_id, name=getattr(agent.cfg, "name", agent_id), type=getattr(agent.cfg, "agent_id", ""), description=getattr(agent.cfg, "description", ""), capabilities=getattr(agent.cfg, "capabilities", []), status="active")
        agents.append(info)
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/{agent_type}", response_model=AgentInfo)
async def get_agent(agent_type: str):
    agent = orchestrator.get(agent_type)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    info = AgentInfo(agent_id=agent_type, name=getattr(agent.cfg, "name", agent_type), type=getattr(agent.cfg, "agent_id", agent_type), description=getattr(agent.cfg, "description", ""), capabilities=getattr(agent.cfg, "capabilities", []), status="active")
    return info


@router.post("/invoke", response_model=AgentResponse)
async def invoke_agent(req: AgentRequest):
    start = time.time()
    agent = orchestrator.get(req.agent_type)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not registered")

    try:
        result = await orchestrator.invoke(req.agent_type, req.input_data)
        duration = time.time() - start
        return AgentResponse(agent_id=req.agent_type, result=result, execution_time=duration, status="success")
    except Exception as exc:
        duration = time.time() - start
        return AgentResponse(agent_id=req.agent_type, result={}, execution_time=duration, status="error", error=str(exc))


@router.get("/health")
async def agents_health():
    # Basic health: report the registry statuses
    return {k: {"status": "active"} for k in orchestrator.registry.keys()}
