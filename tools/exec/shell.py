"""
LEGIONGASPER v2.0 - Shell Execution Tool
OpenClaw-compatible shell execution with sandboxing
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import subprocess
import shlex
import os
import json
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class ShellResult:
    """Result of shell command execution"""
    command: str
    stdout: str
    stderr: str
    returncode: int
    execution_time: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp
        }

class ShellExecutor:
    """Sandboxed shell command executor"""
    
    def __init__(self, 
                 allowed_commands: Optional[List[str]] = None,
                 blocked_commands: Optional[List[str]] = None,
                 timeout: int = 30,
                 working_dir: Optional[str] = None):
        self.allowed_commands = allowed_commands or []
        self.blocked_commands = blocked_commands or ['rm -rf /', 'mkfs', 'dd if=/dev/zero']
        self.timeout = timeout
        self.working_dir = working_dir or os.getcwd()
        
    def _is_safe(self, command: str) -> bool:
        """Check if command is safe to execute"""
        # Check blocked commands
        for blocked in self.blocked_commands:
            if blocked in command:
                return False
        return True
    
    def execute(self, command: str, 
                cwd: Optional[str] = None,
                env: Optional[Dict[str, str]] = None,
                shell: bool = True) -> ShellResult:
        """Execute shell command"""
        start_time = datetime.now()
        
        if not self._is_safe(command):
            return ShellResult(
                command=command,
                stdout="",
                stderr="Command blocked for security reasons",
                returncode=-1,
                execution_time=0.0,
                timestamp=start_time.isoformat()
            )
        
        try:
            result = subprocess.run(
                command if shell else shlex.split(command),
                shell=shell,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd or self.working_dir,
                env={**os.environ, **(env or {})}
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return ShellResult(
                command=command,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                execution_time=execution_time,
                timestamp=start_time.isoformat()
            )
            
        except subprocess.TimeoutExpired:
            return ShellResult(
                command=command,
                stdout="",
                stderr=f"Command timed out after {self.timeout} seconds",
                returncode=-1,
                execution_time=self.timeout,
                timestamp=start_time.isoformat()
            )
        except Exception as e:
            return ShellResult(
                command=command,
                stdout="",
                stderr=str(e),
                returncode=-1,
                execution_time=0.0,
                timestamp=start_time.isoformat()
            )
    
    async def execute_async(self, command: str,
                          cwd: Optional[str] = None,
                          env: Optional[Dict[str, str]] = None) -> ShellResult:
        """Execute shell command asynchronously"""
        start_time = datetime.now()
        
        if not self._is_safe(command):
            return ShellResult(
                command=command,
                stdout="",
                stderr="Command blocked for security reasons",
                returncode=-1,
                execution_time=0.0,
                timestamp=start_time.isoformat()
            )
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or self.working_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return ShellResult(
                command=command,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                returncode=proc.returncode,
                execution_time=execution_time,
                timestamp=start_time.isoformat()
            )
            
        except asyncio.TimeoutError:
            return ShellResult(
                command=command,
                stdout="",
                stderr=f"Command timed out after {self.timeout} seconds",
                returncode=-1,
                execution_time=self.timeout,
                timestamp=start_time.isoformat()
            )
        except Exception as e:
            return ShellResult(
                command=command,
                stdout="",
                stderr=str(e),
                returncode=-1,
                execution_time=0.0,
                timestamp=start_time.isoformat()
            )

# Global executor instance
_default_executor = ShellExecutor()

def execute(command: str, **kwargs) -> ShellResult:
    """Execute shell command using default executor"""
    return _default_executor.execute(command, **kwargs)

def execute_async(command: str, **kwargs):
    """Execute shell command asynchronously using default executor"""
    return _default_executor.execute_async(command, **kwargs)
