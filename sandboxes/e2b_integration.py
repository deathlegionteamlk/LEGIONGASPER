import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from e2b import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False

class E2BSandbox:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('E2B_API_KEY')
        self.sandboxes: Dict[str, Any] = {}
        self.available = E2B_AVAILABLE
        
    async def create_sandbox(self, template: str = "code-interpreter", timeout: int = 3600) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "e2b package not installed"}
        
        if not self.api_key:
            return {"success": False, "error": "E2B_API_KEY not set"}
        
        try:
            sandbox = Sandbox(template=template, api_key=self.api_key, timeout=timeout)
            sandbox_id = sandbox.id
            
            self.sandboxes[sandbox_id] = {
                "sandbox": sandbox,
                "template": template,
                "created": datetime.now().isoformat(),
                "timeout": timeout
            }
            
            return {
                "success": True,
                "sandbox_id": sandbox_id,
                "template": template,
                "status": "running"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_code(self, sandbox_id: str, code: str, language: str = "python") -> Dict[str, Any]:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        
        sandbox = self.sandboxes[sandbox_id]["sandbox"]
        
        try:
            if language == "python":
                execution = sandbox.run_code(code)
            elif language == "bash":
                execution = sandbox.commands.run(code)
            else:
                return {"success": False, "error": f"Unsupported language: {language}"}
            
            return {
                "success": True,
                "stdout": execution.stdout if hasattr(execution, 'stdout') else str(execution),
                "stderr": execution.stderr if hasattr(execution, 'stderr') else "",
                "exit_code": execution.exit_code if hasattr(execution, 'exit_code') else 0,
                "sandbox_id": sandbox_id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def install_packages(self, sandbox_id: str, packages: List[str]) -> Dict[str, Any]:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        
        sandbox = self.sandboxes[sandbox_id]["sandbox"]
        
        try:
            package_str = " ".join(packages)
            execution = sandbox.commands.run(f"pip install {package_str}")
            
            return {
                "success": True,
                "stdout": execution.stdout,
                "stderr": execution.stderr,
                "packages": packages
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def write_file(self, sandbox_id: str, path: str, content: str) -> Dict[str, Any]:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        
        sandbox = self.sandboxes[sandbox_id]["sandbox"]
        
        try:
            sandbox.files.write(path, content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def read_file(self, sandbox_id: str, path: str) -> Dict[str, Any]:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        
        sandbox = self.sandboxes[sandbox_id]["sandbox"]
        
        try:
            content = sandbox.files.read(path)
            return {"success": True, "content": content, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_files(self, sandbox_id: str, path: str = "/") -> Dict[str, Any]:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        
        sandbox = self.sandboxes[sandbox_id]["sandbox"]
        
        try:
            files = sandbox.files.list(path)
            return {"success": True, "files": files, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self, sandbox_id: str) -> Dict[str, Any]:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        
        try:
            sandbox = self.sandboxes[sandbox_id]["sandbox"]
            sandbox.close()
            del self.sandboxes[sandbox_id]
            return {"success": True, "message": "Sandbox closed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close_all(self):
        for sandbox_id in list(self.sandboxes.keys()):
            await self.close(sandbox_id)
    
    def get_status(self, sandbox_id: str) -> Dict[str, Any]:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        
        info = self.sandboxes[sandbox_id]
        return {
            "success": True,
            "sandbox_id": sandbox_id,
            "template": info["template"],
            "created": info["created"],
            "timeout": info["timeout"]
        }
    
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        return [
            {
                "sandbox_id": sid,
                "template": info["template"],
                "created": info["created"]
            }
            for sid, info in self.sandboxes.items()
        ]

e2b_sandbox = E2BSandbox()
