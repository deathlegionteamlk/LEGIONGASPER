import os
import subprocess
import tempfile
import shutil
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

class VMIsolation:
    def __init__(self):
        self.containers: Dict[str, Dict[str, Any]] = {}
        self.use_docker = self._check_docker()
        
    def _check_docker(self) -> bool:
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def create_container(self, name: Optional[str] = None, image: str = "python:3.11-slim") -> Dict[str, Any]:
        container_id = name or f"vm_{uuid.uuid4().hex[:8]}"
        
        if self.use_docker:
            return await self._create_docker_container(container_id, image)
        else:
            return await self._create_chroot_jail(container_id)
    
    async def _create_docker_container(self, container_id: str, image: str) -> Dict[str, Any]:
        try:
            cmd = [
                'docker', 'run', '-d', '--name', container_id,
                '--memory=512m', '--cpus=1.0',
                '--network=none',
                '-v', f'/tmp/{container_id}:/workspace',
                image, 'sleep', '3600'
            ]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                docker_id = stdout.decode().strip()
                self.containers[container_id] = {
                    "id": docker_id,
                    "type": "docker",
                    "created": datetime.now().isoformat(),
                    "status": "running"
                }
                return {"success": True, "container_id": container_id, "type": "docker"}
            else:
                return {"success": False, "error": stderr.decode()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_chroot_jail(self, container_id: str) -> Dict[str, Any]:
        try:
            jail_path = f"/tmp/chroot_{container_id}"
            os.makedirs(jail_path, exist_ok=True)
            
            # Create minimal filesystem
            dirs = ['bin', 'lib', 'lib64', 'usr', 'tmp', 'workspace', 'dev', 'proc']
            for d in dirs:
                os.makedirs(os.path.join(jail_path, d), exist_ok=True)
            
            # Copy essential binaries
            essential_bins = ['/bin/sh', '/bin/bash', '/bin/ls', '/bin/cat', '/bin/echo', '/bin/mkdir', '/bin/rm']
            for bin_path in essential_bins:
                if os.path.exists(bin_path):
                    dest = os.path.join(jail_path, bin_path.lstrip('/'))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(bin_path, dest)
            
            # Copy libraries
            await self._copy_libs(jail_path, essential_bins)
            
            # Set permissions
            os.chmod(jail_path, 0o755)
            
            self.containers[container_id] = {
                "id": container_id,
                "type": "chroot",
                "path": jail_path,
                "created": datetime.now().isoformat(),
                "status": "ready"
            }
            return {"success": True, "container_id": container_id, "type": "chroot", "path": jail_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _copy_libs(self, jail_path: str, binaries: List[str]):
        libs_copied = set()
        for binary in binaries:
            if not os.path.exists(binary):
                continue
            try:
                result = subprocess.run(['ldd', binary], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '=>' in line:
                            lib_path = line.split('=>')[1].split()[0]
                            if lib_path not in libs_copied and os.path.exists(lib_path):
                                dest = os.path.join(jail_path, lib_path.lstrip('/'))
                                os.makedirs(os.path.dirname(dest), exist_ok=True)
                                shutil.copy2(lib_path, dest)
                                libs_copied.add(lib_path)
            except:
                pass
    
    async def execute(self, container_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        if container_id not in self.containers:
            return {"success": False, "error": "Container not found"}
        
        container = self.containers[container_id]
        
        if container["type"] == "docker":
            return await self._execute_docker(container_id, command, timeout)
        else:
            return await self._execute_chroot(container_id, command, timeout)
    
    async def _execute_docker(self, container_id: str, command: str, timeout: int) -> Dict[str, Any]:
        try:
            cmd = ['docker', 'exec', container_id, 'sh', '-c', command]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
            
            return {
                "success": result.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "returncode": result.returncode
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_chroot(self, container_id: str, command: str, timeout: int) -> Dict[str, Any]:
        try:
            jail_path = self.containers[container_id]["path"]
            
            # Use chroot with unshare for isolation
            cmd = ['sudo', 'unshare', '--pid', '--fork', '--mount-proc', 'chroot', jail_path, 'sh', '-c', command]
            
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
            
            return {
                "success": result.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "returncode": result.returncode
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def destroy(self, container_id: str) -> Dict[str, Any]:
        if container_id not in self.containers:
            return {"success": False, "error": "Container not found"}
        
        container = self.containers[container_id]
        
        if container["type"] == "docker":
            return await self._destroy_docker(container_id)
        else:
            return await self._destroy_chroot(container_id)
    
    async def _destroy_docker(self, container_id: str) -> Dict[str, Any]:
        try:
            cmd = ['docker', 'rm', '-f', container_id]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            del self.containers[container_id]
            return {"success": True, "message": "Docker container destroyed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _destroy_chroot(self, container_id: str) -> Dict[str, Any]:
        try:
            jail_path = self.containers[container_id]["path"]
            if os.path.exists(jail_path):
                shutil.rmtree(jail_path)
            del self.containers[container_id]
            return {"success": True, "message": "Chroot jail destroyed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def status(self, container_id: str) -> Dict[str, Any]:
        if container_id not in self.containers:
            return {"success": False, "error": "Container not found"}
        return {"success": True, "container": self.containers[container_id]}
    
    def list_containers(self) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in self.containers.items()]
    
    async def write_file(self, container_id: str, path: str, content: str) -> Dict[str, Any]:
        if container_id not in self.containers:
            return {"success": False, "error": "Container not found"}
        
        container = self.containers[container_id]
        
        try:
            if container["type"] == "docker":
                # Write to mounted volume
                full_path = f"/tmp/{container_id}/{path}"
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
            else:
                full_path = os.path.join(container["path"], path.lstrip('/'))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def read_file(self, container_id: str, path: str) -> Dict[str, Any]:
        if container_id not in self.containers:
            return {"success": False, "error": "Container not found"}
        
        container = self.containers[container_id]
        
        try:
            if container["type"] == "docker":
                full_path = f"/tmp/{container_id}/{path}"
            else:
                full_path = os.path.join(container["path"], path.lstrip('/'))
            
            with open(full_path, 'r') as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

vm_isolation = VMIsolation()
