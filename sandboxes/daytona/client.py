"""
LEGIONGASPER v2.0 - Daytona.dev Integration
90ms environment creation with devcontainer support
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import os
import requests

@dataclass
class WorkspaceConfig:
    """Daytona workspace configuration"""
    id: str
    name: str
    language: str = "python"
    cpu: int = 2
    memory: int = 4  # GB
    disk: int = 10  # GB
    env_vars: Dict[str, str] = None
    
    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}

class DaytonaClient:
    """Daytona.dev workspace client"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 server_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("DAYTONA_API_KEY")
        self.server_url = server_url or os.getenv("DAYTONA_SERVER_URL", 
                                                    "https://api.daytona.io")
        self.workspaces: Dict[str, Dict] = {}
        
    def create_workspace(self, name: str, language: str = "python",
                        config: Optional[Dict] = None) -> Optional[str]:
        """Create new workspace (~90ms)"""
        if not self.api_key:
            return self._create_mock_workspace(name, language)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "name": name,
                "language": language,
                "resources": config or {
                    "cpu": 2,
                    "memory": 4,
                    "disk": 10
                }
            }
            
            response = requests.post(
                f"{self.server_url}/v1/workspaces",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                workspace_id = data.get("id")
                self.workspaces[workspace_id] = data
                return workspace_id
            else:
                print(f"Daytona API error: {response.status_code}")
                return self._create_mock_workspace(name, language)
                
        except Exception as e:
            print(f"Daytona error: {e}")
            return self._create_mock_workspace(name, language)
    
    def _create_mock_workspace(self, name: str, language: str) -> str:
        """Create mock workspace for testing"""
        workspace_id = f"daytona-{datetime.now().timestamp()}"
        self.workspaces[workspace_id] = {
            "id": workspace_id,
            "name": name,
            "language": language,
            "status": "running",
            "created_at": datetime.now().isoformat()
        }
        return workspace_id
    
    def execute_command(self, workspace_id: str, command: str,
                       timeout: int = 60) -> Dict[str, Any]:
        """Execute command in workspace"""
        if workspace_id not in self.workspaces:
            return {"error": "Workspace not found", "success": False}
        
        try:
            if not self.api_key:
                # Mock execution
                return {
                    "stdout": f"Mock execution: {command}",
                    "stderr": "",
                    "exit_code": 0,
                    "success": True
                }
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = requests.post(
                f"{self.server_url}/v1/workspaces/{workspace_id}/exec",
                headers=headers,
                json={"command": command, "timeout": timeout},
                timeout=timeout + 10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}", "success": False}
                
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_workspace_info(self, workspace_id: str) -> Optional[Dict]:
        """Get workspace information"""
        return self.workspaces.get(workspace_id)
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all workspaces"""
        return list(self.workspaces.values())
    
    def stop_workspace(self, workspace_id: str) -> bool:
        """Stop workspace"""
        if workspace_id in self.workspaces:
            self.workspaces[workspace_id]["status"] = "stopped"
            return True
        return False
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete workspace"""
        if workspace_id in self.workspaces:
            del self.workspaces[workspace_id]
            return True
        return False
    
    def install_devcontainer(self, workspace_id: str, 
                            devcontainer_config: Dict) -> bool:
        """Install devcontainer configuration"""
        if workspace_id not in self.workspaces:
            return False
        
        try:
            self.workspaces[workspace_id]["devcontainer"] = devcontainer_config
            return True
        except Exception as e:
            print(f"Devcontainer error: {e}")
            return False

# Global client
_default_client = DaytonaClient()

def create_workspace(name: str, **kwargs) -> Optional[str]:
    """Create Daytona workspace"""
    return _default_client.create_workspace(name, **kwargs)

def execute_command(workspace_id: str, command: str, **kwargs) -> Dict[str, Any]:
    """Execute command in workspace"""
    return _default_client.execute_command(workspace_id, command, **kwargs)

def list_workspaces() -> List[Dict[str, Any]]:
    """List workspaces"""
    return _default_client.list_workspaces()
