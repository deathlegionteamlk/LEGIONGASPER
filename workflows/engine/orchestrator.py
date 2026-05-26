"""
LEGIONGASPER v2.0 - Lobster-like Workflow Orchestration
State management and workflow execution
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

class WorkflowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NodeState(Enum):
    IDLE = "idle"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowNode:
    """Workflow node"""
    id: str
    type: str  # task, condition, loop, parallel, trigger
    config: Dict[str, Any]
    state: NodeState = NodeState.IDLE
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class Workflow:
    """Workflow definition"""
    id: str
    name: str
    nodes: Dict[str, WorkflowNode]
    edges: List[Dict[str, str]]
    state: WorkflowState = WorkflowState.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class WorkflowOrchestrator:
    """Lobster-like workflow orchestrator"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.executors: Dict[str, Callable] = {}
        self._running: Dict[str, asyncio.Task] = {}
        
    def register_executor(self, node_type: str, 
                         executor: Callable) -> None:
        """Register node executor"""
        self.executors[node_type] = executor
    
    def create_workflow(self, name: str, 
                       nodes: List[Dict],
                       edges: List[Dict]) -> str:
        """Create new workflow"""
        workflow_id = f"wf_{datetime.now().timestamp()}"
        
        node_objects = {}
        for node_data in nodes:
            node = WorkflowNode(
                id=node_data["id"],
                type=node_data["type"],
                config=node_data.get("config", {}),
                inputs=node_data.get("inputs", []),
                outputs=node_data.get("outputs", [])
            )
            node_objects[node.id] = node
        
        workflow = Workflow(
            id=workflow_id,
            name=name,
            nodes=node_objects,
            edges=edges
        )
        
        self.workflows[workflow_id] = workflow
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str,
                              context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute workflow"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        workflow.state = WorkflowState.RUNNING
        workflow.started_at = datetime.now().isoformat()
        if context:
            workflow.context.update(context)
        
        try:
            # Find start nodes (no inputs)
            start_nodes = [
                n for n in workflow.nodes.values()
                if not n.inputs
            ]
            
            # Execute in topological order
            executed = set()
            pending = set(workflow.nodes.keys())
            
            while pending:
                # Find nodes ready to execute
                ready = [
                    nid for nid in pending
                    if all(inp in executed for inp in workflow.nodes[nid].inputs)
                ]
                
                if not ready:
                    break
                
                # Execute ready nodes
                tasks = [
                    self._execute_node(workflow, workflow.nodes[nid])
                    for nid in ready
                ]
                
                await asyncio.gather(*tasks)
                
                for nid in ready:
                    executed.add(nid)
                    pending.remove(nid)
            
            workflow.state = WorkflowState.COMPLETED
            workflow.completed_at = datetime.now().isoformat()
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "state": workflow.state.value,
                "results": {
                    nid: node.result
                    for nid, node in workflow.nodes.items()
                }
            }
            
        except Exception as e:
            workflow.state = WorkflowState.FAILED
            return {"success": False, "error": str(e)}
    
    async def _execute_node(self, workflow: Workflow, 
                           node: WorkflowNode) -> None:
        """Execute single node"""
        node.state = NodeState.EXECUTING
        node.started_at = datetime.now().isoformat()
        
        try:
            executor = self.executors.get(node.type)
            if executor:
                # Gather inputs from previous nodes
                inputs = {}
                for input_id in node.inputs:
                    if input_id in workflow.nodes:
                        inputs[input_id] = workflow.nodes[input_id].result
                
                result = await executor(node.config, inputs, workflow.context)
                node.result = result
                node.state = NodeState.COMPLETED
            else:
                node.state = NodeState.SKIPPED
                
        except Exception as e:
            node.state = NodeState.FAILED
            node.error = str(e)
        
        node.completed_at = datetime.now().isoformat()
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause workflow execution"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].state = WorkflowState.PAUSED
            return True
        return False
    
    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume workflow execution"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].state = WorkflowState.RUNNING
            return True
        return False
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel workflow"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].state = WorkflowState.CANCELLED
            if workflow_id in self._running:
                self._running[workflow_id].cancel()
            return True
        return False
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow status"""
        if workflow_id not in self.workflows:
            return None
        
        wf = self.workflows[workflow_id]
        return {
            "id": wf.id,
            "name": wf.name,
            "state": wf.state.value,
            "created_at": wf.created_at,
            "started_at": wf.started_at,
            "completed_at": wf.completed_at,
            "nodes": {
                nid: {
                    "type": n.type,
                    "state": n.state.value,
                    "result": n.result,
                    "error": n.error
                }
                for nid, n in wf.nodes.items()
            }
        }
    
    def list_workflows(self) -> List[Dict]:
        """List all workflows"""
        return [
            {
                "id": wf.id,
                "name": wf.name,
                "state": wf.state.value,
                "created_at": wf.created_at
            }
            for wf in self.workflows.values()
        ]

# Global orchestrator
_default_orchestrator = WorkflowOrchestrator()

def create_workflow(name: str, nodes: List[Dict], 
                   edges: List[Dict]) -> str:
    """Create workflow"""
    return _default_orchestrator.create_workflow(name, nodes, edges)

def execute_workflow(workflow_id: str, **kwargs):
    """Execute workflow"""
    return _default_orchestrator.execute_workflow(workflow_id, **kwargs)
