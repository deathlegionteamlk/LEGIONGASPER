"""
LEGIONGASPER v2.0 - Canvas Visualization Tool
OpenClaw-like canvas for workflow visualization
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class CanvasNode:
    """Canvas node for workflow visualization"""
    id: str
    type: str  # agent, tool, condition, trigger, output
    label: str
    x: float
    y: float
    width: float = 150
    height: float = 80
    color: str = "#3F8694"
    data: Dict = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)

@dataclass
class CanvasEdge:
    """Canvas edge connecting nodes"""
    id: str
    source: str
    target: str
    label: Optional[str] = None
    type: str = "default"  # default, conditional, error
    animated: bool = False

class CanvasRenderer:
    """OpenClaw-like canvas renderer"""
    
    NODE_COLORS = {
        "agent": "#3F8694",
        "tool": "#6B8E23",
        "condition": "#DAA520",
        "trigger": "#9370DB",
        "output": "#CD5C5C",
        "input": "#4682B4",
        "loop": "#FF8C00"
    }
    
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.nodes: Dict[str, CanvasNode] = {}
        self.edges: Dict[str, CanvasEdge] = {}
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
    def add_node(self, node_type: str, label: str, x: float, y: float,
                 node_id: Optional[str] = None, **data) -> str:
        """Add node to canvas"""
        node_id = node_id or f"node_{len(self.nodes)}"
        
        node = CanvasNode(
            id=node_id,
            type=node_type,
            label=label,
            x=x,
            y=y,
            color=self.NODE_COLORS.get(node_type, "#3F8694"),
            data=data
        )
        
        self.nodes[node_id] = node
        return node_id
    
    def add_edge(self, source: str, target: str, 
                 edge_type: str = "default",
                 label: Optional[str] = None,
                 edge_id: Optional[str] = None) -> str:
        """Add edge between nodes"""
        edge_id = edge_id or f"edge_{len(self.edges)}"
        
        edge = CanvasEdge(
            id=edge_id,
            source=source,
            target=target,
            type=edge_type,
            label=label
        )
        
        self.edges[edge_id] = edge
        
        # Update node connections
        if source in self.nodes:
            self.nodes[source].outputs.append(target)
        if target in self.nodes:
            self.nodes[target].inputs.append(source)
        
        return edge_id
    
    def remove_node(self, node_id: str) -> bool:
        """Remove node and connected edges"""
        if node_id not in self.nodes:
            return False
        
        # Remove connected edges
        edges_to_remove = [
            eid for eid, edge in self.edges.items()
            if edge.source == node_id or edge.target == node_id
        ]
        for eid in edges_to_remove:
            del self.edges[eid]
        
        del self.nodes[node_id]
        return True
    
    def move_node(self, node_id: str, x: float, y: float) -> bool:
        """Move node to new position"""
        if node_id not in self.nodes:
            return False
        
        self.nodes[node_id].x = x
        self.nodes[node_id].y = y
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Export canvas to dictionary"""
        return {
            "width": self.width,
            "height": self.height,
            "zoom": self.zoom,
            "pan": {"x": self.pan_x, "y": self.pan_y},
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "x": n.x,
                    "y": n.y,
                    "width": n.width,
                    "height": n.height,
                    "color": n.color,
                    "data": n.data
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "type": e.type,
                    "label": e.label,
                    "animated": e.animated
                }
                for e in self.edges.values()
            ]
        }
    
    def to_json(self) -> str:
        """Export canvas to JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    def from_dict(self, data: Dict[str, Any]) -> bool:
        """Import canvas from dictionary"""
        try:
            self.width = data.get("width", 1200)
            self.height = data.get("height", 800)
            self.zoom = data.get("zoom", 1.0)
            pan = data.get("pan", {})
            self.pan_x = pan.get("x", 0)
            self.pan_y = pan.get("y", 0)
            
            self.nodes = {}
            self.edges = {}
            
            for node_data in data.get("nodes", []):
                node = CanvasNode(
                    id=node_data["id"],
                    type=node_data["type"],
                    label=node_data["label"],
                    x=node_data["x"],
                    y=node_data["y"],
                    width=node_data.get("width", 150),
                    height=node_data.get("height", 80),
                    color=node_data.get("color", "#3F8694"),
                    data=node_data.get("data", {})
                )
                self.nodes[node.id] = node
            
            for edge_data in data.get("edges", []):
                edge = CanvasEdge(
                    id=edge_data["id"],
                    source=edge_data["source"],
                    target=edge_data["target"],
                    type=edge_data.get("type", "default"),
                    label=edge_data.get("label"),
                    animated=edge_data.get("animated", False)
                )
                self.edges[edge.id] = edge
            
            return True
        except Exception as e:
            print(f"Error importing canvas: {e}")
            return False
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get canvas bounds"""
        if not self.nodes:
            return (0, 0, self.width, self.height)
        
        xs = [n.x for n in self.nodes.values()]
        ys = [n.y for n in self.nodes.values()]
        
        return (min(xs), min(ys), max(xs), max(ys))
    
    def auto_layout(self) -> None:
        """Auto-layout nodes in grid"""
        if not self.nodes:
            return
        
        cols = int(len(self.nodes) ** 0.5) + 1
        spacing_x = 200
        spacing_y = 150
        
        for i, node in enumerate(self.nodes.values()):
            row = i // cols
            col = i % cols
            node.x = 100 + col * spacing_x
            node.y = 100 + row * spacing_y

# Global canvas instance
_default_canvas = CanvasRenderer()

def create_canvas(width: int = 1200, height: int = 800) -> CanvasRenderer:
    """Create new canvas"""
    return CanvasRenderer(width, height)

def get_canvas() -> CanvasRenderer:
    """Get default canvas"""
    return _default_canvas
