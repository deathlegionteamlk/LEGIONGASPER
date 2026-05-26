import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from ..core.factory import AgentFactory, get_agent_factory
from ..core.captain import Captain
from ..core.orchestrator import OrchestratorTask, get_orchestrator
from ..core.squad import Squad
from ..governance.audit import get_audit_logger
from ..governance.rbac import get_rbac_manager, Permission
from ..tools.registry import ToolRegistry
from ..tools.builtin import get_builtin_tools
from ..phone.manager import PhoneManager
from ..phone.pgone_manager import PGOneManager
from ..dashboard.phone_dashboard import PhoneDashboard

class SpawnAgentRequest(BaseModel):
    template_id: str
    agent_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = {}

class SubmitTaskRequest(BaseModel):
    description: str
    agent_id: Optional[str] = None
    priority: str = "normal"
    dependencies: Optional[List[str]] = []

class CreateSquadRequest(BaseModel):
    task_description: str
    agent_count: int = 3
    template_ids: Optional[List[str]] = None

class ExecuteToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    agent_id: Optional[str] = "gateway"

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

connected_clients: Dict[str, WebSocket] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    print("🚀 LEGIONGASPER Gateway starting...")
    
    from ..tools.registry import ToolRegistry
    registry = ToolRegistry()
    from ..tools.builtin import register_builtin_tools
    register_builtin_tools(registry)
    app.state.tool_registry = registry
    
    rbac = get_rbac_manager()
    
    phone_manager = PhoneManager()
    pgone_manager = PGOneManager(phone_manager)
    app.state.phone_manager = phone_manager
    app.state.pgone_manager = pgone_manager
    
    phone_dashboard = PhoneDashboard(phone_manager, pgone_manager)
    app.include_router(phone_dashboard.router)
    await phone_dashboard.start_monitoring()
    
    yield
    
    await phone_dashboard.stop_monitoring()
    print("🛑 LEGIONGASPER Gateway shutting down...")

def create_gateway_app() -> FastAPI:
    
    app = FastAPI(
        title="LEGIONGASPER Gateway API",
        description="OpenClaw Factory Edition - Multi-Agent System Gateway",
        version="1.0.0",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        
        return {
            "status": "healthy",
            "service": "legiongasper-gateway",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.post("/api/v1/agents/spawn")
    async def spawn_agent(request: SpawnAgentRequest):
        
        try:
            factory = await get_agent_factory()
            
            agent_id = request.agent_id or f"agent_{uuid.uuid4().hex[:8]}"
            
            agent = await factory.spawn(
                template_id=request.template_id,
                agent_id=agent_id,
                config=request.config
            )
            
            audit = await get_audit_logger()
            await audit.log_agent_spawn(agent_id, request.template_id, "system")
            
            return ApiResponse(
                success=True,
                data={
                    "agent_id": agent_id,
                    "template_id": request.template_id,
                    "status": "spawned"
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.get("/api/v1/agents")
    async def list_agents():
        
        try:
            factory = await get_agent_factory()
            agents = await factory.list_agents()
            
            return ApiResponse(
                success=True,
                data={"agents": agents},
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.get("/api/v1/agents/{agent_id}")
    async def get_agent(agent_id: str):
        
        try:
            factory = await get_agent_factory()
            agent = await factory.get_agent(agent_id)
            
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            return ApiResponse(
                success=True,
                data={
                    "agent_id": agent_id,
                    "status": agent.state.value if hasattr(agent, 'state') else "unknown",
                    "template_id": agent.template_id if hasattr(agent, 'template_id') else "unknown"
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.delete("/api/v1/agents/{agent_id}")
    async def terminate_agent(agent_id: str):
        
        try:
            factory = await get_agent_factory()
            await factory.recycle(agent_id)
            
            return ApiResponse(
                success=True,
                data={"agent_id": agent_id, "status": "terminated"},
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.post("/api/v1/tasks/submit")
    async def submit_task(request: SubmitTaskRequest):
        
        try:
            orchestrator = await get_orchestrator()
            
            task_id = await orchestrator.submit(
                description=request.description,
                agent_id=request.agent_id,
                priority=request.priority,
                dependencies=request.dependencies
            )
            
            return ApiResponse(
                success=True,
                data={
                    "task_id": task_id,
                    "status": "submitted"
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.get("/api/v1/tasks")
    async def list_tasks():
        
        try:
            orchestrator = await get_orchestrator()
            tasks = await orchestrator.list_tasks()
            
            return ApiResponse(
                success=True,
                data={
                    "tasks": [
                        {
                            "task_id": t.task_id,
                            "description": t.description,
                            "status": t.status.value,
                            "priority": t.priority.value
                        }
                        for t in tasks
                    ]
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.get("/api/v1/tasks/{task_id}")
    async def get_task(task_id: str):
        
        try:
            orchestrator = await get_orchestrator()
            task = await orchestrator.get_task(task_id)
            
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return ApiResponse(
                success=True,
                data={
                    "task_id": task.task_id,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "result": task.result
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.post("/api/v1/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str):
        
        try:
            orchestrator = await get_orchestrator()
            success = await orchestrator.cancel(task_id)
            
            return ApiResponse(
                success=success,
                data={"task_id": task_id, "cancelled": success},
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.post("/api/v1/squads/create")
    async def create_squad(request: CreateSquadRequest):
        
        try:
            factory = await get_agent_factory()
            
            squad = Squad(
                squad_id=f"squad_{uuid.uuid4().hex[:8]}",
                max_concurrent=request.agent_count
            )
            
            template_ids = request.template_ids or ["research", "code", "review"]
            for i, template_id in enumerate(template_ids[:request.agent_count]):
                agent = await factory.spawn(
                    template_id=template_id,
                    agent_id=f"{squad.squad_id}_agent_{i}"
                )
                squad.add_agent(agent)
            
            return ApiResponse(
                success=True,
                data={
                    "squad_id": squad.squad_id,
                    "agent_count": len(squad.agents),
                    "task": request.task_description
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.post("/api/v1/tools/execute")
    async def execute_tool(request: ExecuteToolRequest):
        
        try:
            registry = app.state.tool_registry
            
            result = await registry.execute(
                name=request.tool_name,
                agent_id=request.agent_id,
                **request.parameters
            )
            
            return ApiResponse(
                success=result.get("success", False),
                data=result,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.get("/api/v1/tools")
    async def list_tools():
        
        try:
            registry = app.state.tool_registry
            tools = registry.list_tools()
            
            return ApiResponse(
                success=True,
                data={
                    "tools": [
                        {
                            "name": name,
                            "schema": registry.get_openai_schema(name)
                        }
                        for name in tools
                    ]
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.get("/api/v1/stats")
    async def get_stats():
        
        try:
            factory = await get_agent_factory()
            orchestrator = await get_orchestrator()
            
            agents = await factory.list_agents()
            tasks = await orchestrator.get_stats()
            
            return ApiResponse(
                success=True,
                data={
                    "agents": {
                        "total": len(agents),
                        "by_status": {}
                    },
                    "tasks": {
                        "total": tasks.total,
                        "pending": tasks.pending,
                        "running": tasks.running,
                        "completed": tasks.completed,
                        "failed": tasks.failed
                    }
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        
        await websocket.accept()
        client_id = str(uuid.uuid4())
        connected_clients[client_id] = websocket
        
        try:
            await websocket.send_json({
                "type": "connected",
                "client_id": client_id,
                "message": "Connected to LEGIONGASPER Gateway"
            })
            
            while True:
                
                data = await websocket.receive_json()
                
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                
                elif msg_type == "subscribe":
                    channel = data.get("channel")
                    await websocket.send_json({
                        "type": "subscribed",
                        "channel": channel
                    })
                
                elif msg_type == "execute_task":
                    
                    await websocket.send_json({
                        "type": "ack",
                        "message": "Task received"
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}"
                    })
                    
        except WebSocketDisconnect:
            del connected_clients[client_id]
        except Exception:
            if client_id in connected_clients:
                del connected_clients[client_id]
    
    return app

class GatewayServer:
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8081):
        self.host = host
        self.port = port
        self.app = create_gateway_app()
        self.server = None
    
    async def start(self):
        
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        await self.server.serve()
    
    async def stop(self):
        
        if self.server:
            self.server.should_exit = True
    
    def run_sync(self):
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )