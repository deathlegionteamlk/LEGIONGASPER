import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from ..core.factory import get_agent_factory
from ..core.orchestrator import get_orchestrator
from ..governance.cost import get_cost_tracker

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>LEGIONGASPER Dashboard</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
</head>
<body class=\"bg-slate-900 text-white\">
    <div class=\"container mx-auto p-4\">
        <h1 class=\"text-3xl font-bold mb-4\">LEGIONGASPER Dashboard</h1>
        <div id=\"stats\" class=\"grid grid-cols-4 gap-4\"></div>
    </div>
    <script>
        async function fetchStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('stats').innerHTML = `
                <div class=\"bg-slate-800 p-4 rounded\">Agents: ${data.agents}</div>
                <div class=\"bg-slate-800 p-4 rounded\">Tasks: ${data.tasks}</div>
                <div class=\"bg-slate-800 p-4 rounded\">Completed: ${data.completed}</div>
                <div class=\"bg-slate-800 p-4 rounded\">Cost: $${data.cost.toFixed(2)}</div>
            `;
        }
        fetchStats();
        setInterval(fetchStats, 5000);
    </script>
</body>
</html>
""" 

def create_app() -> FastAPI:
    
    app = FastAPI(title="LEGIONGASPER Dashboard")
    
    connected_clients: List[WebSocket] = []
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        
        return HTMLResponse(content=DASHBOARD_HTML)
    
    @app.get("/api/stats")
    async def get_stats():
        
        try:
            factory = await get_agent_factory()
            orchestrator = await get_orchestrator()
            cost_tracker = await get_cost_tracker()
            
            agents = await factory.list_agents()
            tasks = await orchestrator.get_stats()
            cost_stats = cost_tracker.get_stats()
            
            return {
                "agents": len(agents),
                "tasks": tasks.total,
                "completed": tasks.completed,
                "failed": tasks.failed,
                "cost": cost_stats.get("today_cost", 0),
                "requests": cost_stats.get("total_requests", 0),
                "agent_list": [
                    {
                        "agent_id": a["agent_id"],
                        "template_id": a["template_id"],
                        "status": a["status"]
                    }
                    for a in agents[:10]
                ]
            }
        except Exception as e:
            return {
                "agents": 0,
                "tasks": 0,
                "completed": 0,
                "failed": 0,
                "cost": 0,
                "requests": 0,
                "error": str(e),
                "agent_list": []
            }
    
    @app.get("/api/agents")
    async def get_agents():
        
        try:
            factory = await get_agent_factory()
            agents = await factory.list_agents()
            return {"agents": agents}
        except Exception as e:
            return {"agents": [], "error": str(e)}
    
    @app.get("/api/tasks")
    async def get_tasks():
        
        try:
            orchestrator = await get_orchestrator()
            tasks = await orchestrator.list_tasks()
            return {
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "status": t.status.value,
                        "description": t.description[:50]
                    }
                    for t in tasks
                ]
            }
        except Exception as e:
            return {"tasks": [], "error": str(e)}
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        
        await websocket.accept()
        connected_clients.append(websocket)
        
        try:
            while True:
                
                try:
                    factory = await get_agent_factory()
                    orchestrator = await get_orchestrator()
                    cost_tracker = await get_cost_tracker()
                    
                    agents = await factory.list_agents()
                    tasks = await orchestrator.get_stats()
                    cost_stats = cost_tracker.get_stats()
                    
                    await websocket.send_json({
                        "type": "stats",
                        "agents": len(agents),
                        "tasks": tasks.total,
                        "completed": tasks.completed,
                        "failed": tasks.failed,
                        "cost": cost_stats.get("today_cost", 0),
                        "requests": cost_stats.get("total_requests", 0),
                        "agent_list": [
                            {
                                "agent_id": a["agent_id"],
                                "template_id": a["template_id"],
                                "status": a["status"]
                            }
                            for a in agents[:10]
                        ]
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "event",
                        "message": f"Error: {str(e)}",
                        "level": "error"
                    })
                
                await asyncio.sleep(5)  
                
        except WebSocketDisconnect:
            connected_clients.remove(websocket)
        except Exception:
            if websocket in connected_clients:
                connected_clients.remove(websocket)
    
    return app

class DashboardServer:
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = create_app()
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