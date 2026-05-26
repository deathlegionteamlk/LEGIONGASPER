"""
LEGIONGASPER v2.0 - e2b.dev Integration
Secure sandbox code execution
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import os

@dataclass
class SandboxState:
    """e2b sandbox state"""
    id: str
    status: str
    created_at: str
    last_activity: str
    files: List[str]
    env_vars: Dict[str, str]

class E2BClient:
    """e2b.dev sandbox client"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("E2B_API_KEY")
        self.sandboxes: Dict[str, Any] = {}
        self._client = None
        
    def initialize(self) -> bool:
        """Initialize e2b client"""
        try:
            from e2b import Sandbox
            self._client = Sandbox
            return True
        except ImportError:
            print("e2b not installed. Install with: pip install e2b")
            return False
    
    def create_sandbox(self, template: str = "base") -> Optional[str]:
        """Create new sandbox"""
        if not self._client:
            return None
        
        try:
            sandbox = self._client(template)
            sandbox_id = sandbox.id
            self.sandboxes[sandbox_id] = sandbox
            return sandbox_id
        except Exception as e:
            print(f"Error creating sandbox: {e}")
            return None
    
    def execute_code(self, sandbox_id: str, code: str, 
                    language: str = "python") -> Dict[str, Any]:
        """Execute code in sandbox"""
        if sandbox_id not in self.sandboxes:
            return {"error": "Sandbox not found"}
        
        try:
            sandbox = self.sandboxes[sandbox_id]
            
            if language == "python":
                result = sandbox.run_python(code)
            else:
                result = sandbox.process.start(f"{language} -c '{code}'")
            
            return {
                "stdout": result.stdout if hasattr(result, 'stdout') else str(result),
                "stderr": result.stderr if hasattr(result, 'stderr') else "",
                "exit_code": result.exit_code if hasattr(result, 'exit_code') else 0,
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def install_dependencies(self, sandbox_id: str, 
                           packages: List[str]) -> bool:
        """Install Python packages in sandbox"""
        if sandbox_id not in self.sandboxes:
            return False
        
        try:
            sandbox = self.sandboxes[sandbox_id]
            sandbox.install_packages(packages)
            return True
        except Exception as e:
            print(f"Error installing packages: {e}")
            return False
    
    def write_file(self, sandbox_id: str, path: str, 
                   content: str) -> bool:
        """Write file to sandbox"""
        if sandbox_id not in self.sandboxes:
            return False
        
        try:
            sandbox = self.sandboxes[sandbox_id]
            sandbox.filesystem.write(path, content)
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
    
    def read_file(self, sandbox_id: str, path: str) -> Optional[str]:
        """Read file from sandbox"""
        if sandbox_id not in self.sandboxes:
            return None
        
        try:
            sandbox = self.sandboxes[sandbox_id]
            return sandbox.filesystem.read(path)
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Destroy sandbox"""
        if sandbox_id not in self.sandboxes:
            return False
        
        try:
            sandbox = self.sandboxes[sandbox_id]
            sandbox.close()
            del self.sandboxes[sandbox_id]
            return True
        except Exception as e:
            print(f"Error destroying sandbox: {e}")
            return False
    
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List active sandboxes"""
        return [
            {
                "id": sid,
                "status": "active"
            }
            for sid in self.sandboxes.keys()
        ]

# Global client instance
_default_client = E2BClient()

def create_sandbox(**kwargs) -> Optional[str]:
    """Create new e2b sandbox"""
    return _default_client.create_sandbox(**kwargs)

def execute_code(sandbox_id: str, code: str, **kwargs) -> Dict[str, Any]:
    """Execute code in sandbox"""
    return _default_client.execute_code(sandbox_id, code, **kwargs)

def destroy_sandbox(sandbox_id: str) -> bool:
    """Destroy sandbox"""
    return _default_client.destroy_sandbox(sandbox_id)
