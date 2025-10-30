from fastapi import APIRouter, HTTPException
from typing import List
import time

from ..models.agent import AgentListResponse, AgentInfo, AgentRequest, AgentResponse, WorkflowExecutionRequest, WorkflowExecutionResponse, WorkflowStateUpdate, AgentMessageRequest, AgentMessageResponse, WorkflowVisualizationResponse
from ..config import settings
from ..agents.orchestrator import orchestrator
from ..utils.supabase_client import get_supabase_client
from datetime import datetime

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents():
    agents = []
    for agent_id, agent in orchestrator.registry.items():
        info = AgentInfo(agent_id=agent_id, name=getattr(agent.config, "name", agent_id), type=getattr(agent.config, "agent_id", ""), description=getattr(agent.config, "description", ""), capabilities=getattr(agent.config, "capabilities", []), status="active")
        agents.append(info)
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/{agent_type}", response_model=AgentInfo)
async def get_agent(agent_type: str):
    agent = orchestrator.get(agent_type)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    info = AgentInfo(agent_id=agent_type, name=getattr(agent.config, "name", agent_type), type=getattr(agent.config, "agent_id", agent_type), description=getattr(agent.config, "description", ""), capabilities=getattr(agent.config, "capabilities", []), status="active")
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


@router.post("/workflows/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(req: WorkflowExecutionRequest):
    # Validate participating agents
    for agent in req.participating_agents:
        if agent not in orchestrator.registry:
            raise HTTPException(status_code=400, detail=f"Agent {agent} not found")
    
    try:
        if req.workflow_type == "multi_agent":
            result = await orchestrator.multi_agent_workflow(req.input_data, req.conversation_id, True, True, True)
        elif req.workflow_type == "conditional":
            result = await orchestrator.conditional_workflow(req.conversation_id, req.participating_agents[0] if req.participating_agents else "chat", req.workflow_config, req.input_data)
        elif req.workflow_type == "sequential":
            result = await orchestrator.multi_agent_workflow(req.input_data, req.conversation_id, True, True, True)
        else:
            raise HTTPException(status_code=400, detail="Invalid workflow_type")
        
        # Fetch workflow details
        supabase = get_supabase_client()
        workflow = await supabase.table("workflow_executions").select("*").eq("id", result["workflow_id"]).execute()
        if not workflow.data:
            raise HTTPException(status_code=500, detail="Workflow created but not found")
        
        wf = workflow.data[0]
        execution_time_ms = None
        if wf.get("completed_at") and wf.get("started_at"):
            started = datetime.fromisoformat(wf["started_at"].replace('Z', '+00:00'))
            completed = datetime.fromisoformat(wf["completed_at"].replace('Z', '+00:00'))
            execution_time_ms = int((completed - started).total_seconds() * 1000)
        
        return WorkflowExecutionResponse(
            workflow_id=wf["id"],
            conversation_id=wf["conversation_id"],
            workflow_type=wf["workflow_type"],
            current_state=wf["current_state"],
            current_step=wf.get("current_step"),
            participating_agents=wf["participating_agents"],
            results=wf.get("results", {}),
            started_at=wf["started_at"],
            completed_at=wf.get("completed_at"),
            execution_time_ms=execution_time_ms,
            error_message=wf.get("error_message")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}", response_model=WorkflowExecutionResponse)
async def get_workflow(workflow_id: str):
    supabase = get_supabase_client()
    workflow = await supabase.table("workflow_executions").select("*").eq("id", workflow_id).execute()
    if not workflow.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf = workflow.data[0]
    execution_time_ms = None
    if wf.get("completed_at") and wf.get("started_at"):
        started = datetime.fromisoformat(wf["started_at"].replace('Z', '+00:00'))
        completed = datetime.fromisoformat(wf["completed_at"].replace('Z', '+00:00'))
        execution_time_ms = int((completed - started).total_seconds() * 1000)
    
    return WorkflowExecutionResponse(
        workflow_id=wf["id"],
        conversation_id=wf["conversation_id"],
        workflow_type=wf["workflow_type"],
        current_state=wf["current_state"],
        current_step=wf.get("current_step"),
        participating_agents=wf["participating_agents"],
        results=wf.get("results", {}),
        started_at=wf["started_at"],
        completed_at=wf.get("completed_at"),
        execution_time_ms=execution_time_ms,
        error_message=wf.get("error_message")
    )


@router.get("/workflows/{workflow_id}/visualization", response_model=WorkflowVisualizationResponse)
async def get_workflow_visualization(workflow_id: str):
    supabase = get_supabase_client()
    workflow = await supabase.table("workflow_executions").select("*").eq("id", workflow_id).execute()
    if not workflow.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf = workflow.data[0]
    conversation_id = wf["conversation_id"]
    
    # Query agent logs for timeline
    logs = await supabase.table("agent_logs").select("*").eq("conversation_id", conversation_id).execute()
    execution_timeline = [
        {"timestamp": log["created_at"], "event": log["action"], "agent": log["agent_type"]}
        for log in logs.data
    ]
    
    # Query agent messages
    messages = await supabase.table("agent_messages").select("*").eq("workflow_execution_id", workflow_id).execute()
    agent_interactions = [
        {"from_agent": msg["from_agent"], "to_agent": msg["to_agent"], "message_type": msg["message_type"], "timestamp": msg["created_at"]}
        for msg in messages.data
    ]
    
    # Execution graph
    nodes = wf["participating_agents"]
    edges = [
        {"from": msg["from_agent"], "to": msg["to_agent"], "type": msg["message_type"]}
        for msg in messages.data
    ]
    execution_graph = {"nodes": nodes, "edges": edges}
    
    # Shared memory keys
    memory = await supabase.table("shared_memory").select("memory_key").eq("workflow_execution_id", workflow_id).execute()
    shared_memory_keys = [m["memory_key"] for m in memory.data]
    
    return WorkflowVisualizationResponse(
        workflow_id=workflow_id,
        conversation_id=conversation_id,
        workflow_type=wf["workflow_type"],
        current_state=wf["current_state"],
        execution_timeline=execution_timeline,
        agent_interactions=agent_interactions,
        shared_memory_keys=shared_memory_keys,
        execution_graph=execution_graph
    )


@router.post("/workflows/{workflow_id}/messages", response_model=AgentMessageResponse)
async def send_workflow_message(workflow_id: str, req: AgentMessageRequest):
    supabase = get_supabase_client()
    workflow = await supabase.table("workflow_executions").select("current_state").eq("id", workflow_id).execute()
    if not workflow.data or workflow.data[0]["current_state"] != "running":
        raise HTTPException(status_code=400, detail="Workflow not running")
    
    message_id = await orchestrator.send_agent_message(workflow_id, req.from_agent, req.to_agent, req.message_type, req.content, req.metadata)
    
    return AgentMessageResponse(
        message_id=message_id,
        workflow_execution_id=workflow_id,
        from_agent=req.from_agent,
        to_agent=req.to_agent,
        message_type=req.message_type,
        content=req.content,
        status="pending",
        created_at=datetime.utcnow().isoformat(),
        processed_at=None
    )


@router.get("/workflows/{workflow_id}/messages", response_model=List[AgentMessageResponse])
async def get_workflow_messages(
    workflow_id: str,
    from_agent: str = None,
    to_agent: str = None,
    message_type: str = None,
    status: str = None
):
    supabase = get_supabase_client()
    query = supabase.table("agent_messages").select("*").eq("workflow_execution_id", workflow_id)
    if from_agent:
        query = query.eq("from_agent", from_agent)
    if to_agent:
        query = query.eq("to_agent", to_agent)
    if message_type:
        query = query.eq("message_type", message_type)
    if status:
        query = query.eq("status", status)
    
    messages = await query.execute()
    
    return [
        AgentMessageResponse(
            message_id=msg["id"],
            workflow_execution_id=msg["workflow_execution_id"],
            from_agent=msg["from_agent"],
            to_agent=msg["to_agent"],
            message_type=msg["message_type"],
            content=msg["content"],
            status=msg["status"],
            created_at=msg["created_at"],
            processed_at=msg.get("processed_at")
        )
        for msg in messages.data
    ]


@router.patch("/workflows/{workflow_id}/state", response_model=WorkflowExecutionResponse)
async def update_workflow_state(workflow_id: str, req: WorkflowStateUpdate):
    # TODO: Add authentication check for admin users
    await orchestrator.update_workflow_state(workflow_id, req.current_state, req.current_step)
    
    supabase = get_supabase_client()
    workflow = await supabase.table("workflow_executions").select("*").eq("id", workflow_id).execute()
    if not workflow.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf = workflow.data[0]
    execution_time_ms = None
    if wf.get("completed_at") and wf.get("started_at"):
        started = datetime.fromisoformat(wf["started_at"].replace('Z', '+00:00'))
        completed = datetime.fromisoformat(wf["completed_at"].replace('Z', '+00:00'))
        execution_time_ms = int((completed - started).total_seconds() * 1000)
    
    return WorkflowExecutionResponse(
        workflow_id=wf["id"],
        conversation_id=wf["conversation_id"],
        workflow_type=wf["workflow_type"],
        current_state=wf["current_state"],
        current_step=wf.get("current_step"),
        participating_agents=wf["participating_agents"],
        results=wf.get("results", {}),
        started_at=wf["started_at"],
        completed_at=wf.get("completed_at"),
        execution_time_ms=execution_time_ms,
        error_message=wf.get("error_message")
    )


@router.get("/workflows", response_model=List[WorkflowExecutionResponse])
async def list_workflows(
    conversation_id: str = None,
    workflow_type: str = None,
    current_state: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 50,
    offset: int = 0
):
    supabase = get_supabase_client()
    query = supabase.table("workflow_executions").select("*")
    if conversation_id:
        query = query.eq("conversation_id", conversation_id)
    if workflow_type:
        query = query.eq("workflow_type", workflow_type)
    if current_state:
        query = query.eq("current_state", current_state)
    if start_date:
        query = query.gte("started_at", start_date)
    if end_date:
        query = query.lte("started_at", end_date)
    
    query = query.range(offset, offset + limit - 1)
    workflows = await query.execute()
    
    result = []
    for wf in workflows.data:
        execution_time_ms = None
        if wf.get("completed_at") and wf.get("started_at"):
            started = datetime.fromisoformat(wf["started_at"].replace('Z', '+00:00'))
            completed = datetime.fromisoformat(wf["completed_at"].replace('Z', '+00:00'))
            execution_time_ms = int((completed - started).total_seconds() * 1000)
        
        result.append(WorkflowExecutionResponse(
            workflow_id=wf["id"],
            conversation_id=wf["conversation_id"],
            workflow_type=wf["workflow_type"],
            current_state=wf["current_state"],
            current_step=wf.get("current_step"),
            participating_agents=wf["participating_agents"],
            results=wf.get("results", {}),
            started_at=wf["started_at"],
            completed_at=wf.get("completed_at"),
            execution_time_ms=execution_time_ms,
            error_message=wf.get("error_message")
        ))
    
    return result
