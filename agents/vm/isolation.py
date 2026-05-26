"""
LEGIONGASPER v2.0 - VM Isolation per Agent
Capy.ai-style isolated execution environments
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import subprocess
import os
import tempfile
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import shutil

@dataclass
class VMConfig:
    """VM configuration"""
    cpu_limit: int = 2
    memory_limit: str = "2g"
    disk_limit: str = "10g"
    network_enabled: bool = True
    privileged: bool = False
    env_vars: Dict[str, str] = None
    
    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}

class VMIsolation:
    """VM isolation for agents using Docker/containers"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.container_id: Optional[str] = None
        self.work_dir = tempfile.mkdtemp(prefix=f"legion_{agent_id}_")
        self.config: Optional[VMConfig] = None
        self.created_at = datetime.now().isoformat()
        
    def create_container(self, config: Optional[VMConfig] = None) -> bool:
        """Create isolated container for agent"""
        self.config = config or VMConfig()
        
        try:
            # Check if Docker is available
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Fallback to chroot-based isolation
                return self._create_chroot_jail()
            
            # Create Docker container
            container_name = f"legion-agent-{self.agent_id}"
            
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "--memory", self.config.memory_limit,
                "--cpus", str(self.config.cpu_limit),
                "--network", "bridge" if self.config.network_enabled else "none",
                "-v", f"{self.work_dir}:/workspace",
                "-w", "/workspace",
                "python:3.11-slim",
                "sleep", "infinity"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.container_id = result.stdout.strip()
                return True
            else:
                print(f"Docker error: {result.stderr}")
                return self._create_chroot_jail()
                
        except Exception as e:
            print(f"Container creation error: {e}")
            return self._create_chroot_jail()
    
    def _create_chroot_jail(self) -> bool:
        """Fallback: Create chroot jail"""
        try:
            # Create minimal chroot environment
            dirs = ["bin", "lib", "lib64", "usr", "workspace"]
            for d in dirs:
                os.makedirs(os.path.join(self.work_dir, d), exist_ok=True)
            
            self.container_id = f"chroot-{self.agent_id}"
            return True
        except Exception as e:
            print(f"Chroot creation error: {e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute command in isolated environment"""
        if not self.container_id:
            return {"error": "Container not created", "success": False}
        
        try:
            if self.container_id.startswith("chroot-"):
                # Chroot execution
                cmd = ["chroot", self.work_dir, "/bin/sh", "-c", command]
            else:
                # Docker execution
                cmd = ["docker", "exec", self.container_id, "/bin/sh", "-c", command]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def write_file(self, path: str, content: str) -> bool:
        """Write file to isolated environment"""
        try:
            full_path = os.path.join(self.work_dir, path.lstrip("/"))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Write error: {e}")
            return False
    
    def read_file(self, path: str) -> Optional[str]:
        """Read file from isolated environment"""
        try:
            full_path = os.path.join(self.work_dir, path.lstrip("/"))
            
            with open(full_path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def destroy(self) -> bool:
        """Destroy isolated environment"""
        try:
            if self.container_id and not self.container_id.startswith("chroot-"):
                subprocess.run(
                    ["docker", "rm", "-f", self.container_id],
                    capture_output=True
                )
            
            # Cleanup work directory
            if os.path.exists(self.work_dir):
                shutil.rmtree(self.work_dir)
            
            self.container_id = None
            return True
        except Exception as e:
            print(f"Destroy error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get VM status"""
        return {
            "agent_id": self.agent_id,
            "container_id": self.container_id,
            "work_dir": self.work_dir,
            "created_at": self.created_at,
            "config": {
                "cpu_limit": self.config.cpu_limit if self.config else None,
                "memory_limit": self.config.memory_limit if self.config else None,
                "network_enabled": self.config.network_enabled if self.config else None
            }
        }

class VMManager:
    """Manages VM isolation for all agents"""
    
    def __init__(self):
        self.vms: Dict[str, VMIsolation] = {}
    
    def create_vm(self, agent_id: str, config: Optional[VMConfig] = None) -> VMIsolation:
        """Create VM for agent"""
        vm = VMIsolation(agent_id)
        vm.create_container(config)
        self.vms[agent_id] = vm
        return vm
    
    def get_vm(self, agent_id: str) -> Optional[VMIsolation]:
        """Get VM for agent"""
        return self.vms.get(agent_id)
    
    def destroy_vm(self, agent_id: str) -> bool:
        """Destroy VM for agent"""
        if agent_id in self.vms:
            self.vms[agent_id].destroy()
            del self.vms[agent_id]
            return True
        return False
    
    def list_vms(self) -> List[Dict[str, Any]]:
        """List all VMs"""
        return [vm.get_status() for vm in self.vms.values()]

# Global manager
_default_manager = VMManager()

def create_vm(agent_id: str, **kwargs) -> VMIsolation:
    """Create VM for agent"""
    config = VMConfig(**kwargs) if kwargs else None
    return _default_manager.create_vm(agent_id, config)

def get_vm(agent_id: str) -> Optional[VMIsolation]:
    """Get VM for agent"""
    return _default_manager.get_vm(agent_id)
