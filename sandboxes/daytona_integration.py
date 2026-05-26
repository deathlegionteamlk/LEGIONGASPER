import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from daytona_sdk import Daytona, DaytonaConfig
    DAYTONA_AVAILABLE = True
except ImportError:
    DAYTONA_AVAILABLE = False

class DaytonaWorkspace:
    def __init__(self, api_key: Optional[str] = None, server_url: Optional[str] = None):
        self.api_key = api_key or os.getenv('DAYTONA_API_KEY')
        self.server_url = server_url or os.getenv('DAYTONA_SERVER_URL', 'https://api.daytona.io')
        self.daytona = None
        self.workspaces: Dict[str, Any] = {}
        self.available = DAYTONA_AVAILABLE
        
        if self.available and self.api_key:
            try:
                config = DaytonaConfig(api_key=self.api_key, server_url=self.server_url)
                self.daytona = Daytona(config)
            except Exception as e:
                print(f"Daytona init error: {e}")
                self.available = False
    
    async def create_workspace(self, language: str = "python", target: str = "us") -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "daytona-sdk not installed"}
        
        if not self.api_key:
            return {"success": False, "error": "DAYTONA_API_KEY not set"}
        
        try:
            # Create workspace using Daytona SDK
            workspace = self.daytona.create(params={
                "language": language,
                "target": target
            })
            
            workspace_id = workspace.id
            self.workspaces[workspace_id] = {
                "workspace": workspace,
                "language": language,
                "target": target,
                "created": datetime.now().isoformat(),
                "status": "running"
            }
            
            return {
                "success": True,
                "workspace_id": workspace_id,
                "language": language,
                "target": target,
                "status": "running"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_workspace(self, workspace_id: str) -> Dict[str, Any]:
        if workspace_id not in self.workspaces:
            return {"success": False, "error": "Workspace not found"}
        
        try:
            workspace = self.workspaces[workspace_id]["workspace"]
            self.daytona.remove(workspace)
            del self.workspaces[workspace_id]
            return {"success": True, "message": "Workspace deleted"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_command(self, workspace_id: str, command: str, timeout: int = 60) -> Dict[str, Any]:
        if workspace_id not in self.workspaces:
            return {"success": False, "error": "Workspace not found"}
        
        workspace = self.workspaces[workspace_id]["workspace"]
        
        try:
            response = workspace.process.execute(command, timeout=timeout)
            
            return {
                "success": True,
                "stdout": response.result if hasattr(response, 'result') else str(response),
                "exit_code": response.exit_code if hasattr(response, 'exit_code') else 0,
                "workspace_id": workspace_id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_file(self, workspace_id: str, path: str) -> Dict[str, Any]:
        if workspace_id not in self.workspaces:
            return {"success": False, "error": "Workspace not found"}
        
        workspace = self.workspaces[workspace_id]["workspace"]
        
        try:
            content = workspace.fs.download_file(path)
            return {
                "success": True,
                "content": content.decode('utf-8') if isinstance(content, bytes) else content,
                "path": path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def put_file(self, workspace_id: str, path: str, content: str) -> Dict[str, Any]:
        if workspace_id not in self.workspaces:
            return {"success": False, "error": "Workspace not found"}
        
        workspace = self.workspaces[workspace_id]["workspace"]
        
        try:
            workspace.fs.upload_file(path, content.encode('utf-8') if isinstance(content, str) else content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_workspaces(self) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "daytona-sdk not installed"}
        
        try:
            workspaces = self.daytona.list()
            return {
                "success": True,
                "workspaces": [
                    {
                        "id": w.id,
                        "language": getattr(w, 'language', 'unknown'),
                        "target": getattr(w, 'target', 'unknown'),
                        "state": getattr(w, 'state', 'unknown')
                    }
                    for w in workspaces
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self, workspace_id: str) -> Dict[str, Any]:
        if workspace_id not in self.workspaces:
            return {"success": False, "error": "Workspace not found"}
        
        info = self.workspaces[workspace_id]
        return {
            "success": True,
            "workspace_id": workspace_id,
            "language": info["language"],
            "target": info["target"],
            "created": info["created"],
            "status": info["status"]
        }
    
    def get_workspace_info(self, workspace_id: str) -> Dict[str, Any]:
        return self.get_status(workspace_id)

daytona_workspace = DaytonaWorkspace()
