"""
LEGIONGASPER v2.0 - Git Branch Management
Capy.ai-style Git branch per agent
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import subprocess
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BranchInfo:
    """Git branch information"""
    name: str
    commit: str
    author: str
    last_commit_date: str
    is_remote: bool
    ahead: int = 0
    behind: int = 0

class GitBranchManager:
    """Manage Git branches per agent"""
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getcwd()
        self.agent_branches: Dict[str, str] = {}
        
    def _run_git(self, args: List[str], cwd: Optional[str] = None) -> tuple:
        """Run git command"""
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=cwd or self.repo_path
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def create_branch(self, branch_name: str, 
                     base: str = "main") -> bool:
        """Create new branch"""
        # Checkout base
        self._run_git(["checkout", base])
        # Create and checkout new branch
        code, _, err = self._run_git(["checkout", "-b", branch_name])
        if code != 0:
            print(f"Error creating branch: {err}")
            return False
        return True
    
    def create_agent_branch(self, agent_id: str) -> Optional[str]:
        """Create branch for agent"""
        branch_name = f"agent/{agent_id}"
        if self.create_branch(branch_name):
            self.agent_branches[agent_id] = branch_name
            return branch_name
        return None
    
    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout branch"""
        code, _, _ = self._run_git(["checkout", branch_name])
        return code == 0
    
    def delete_branch(self, branch_name: str, 
                     force: bool = False) -> bool:
        """Delete branch"""
        flag = "-D" if force else "-d"
        code, _, _ = self._run_git(["branch", flag, branch_name])
        return code == 0
    
    def list_branches(self) -> List[BranchInfo]:
        """List all branches"""
        code, stdout, _ = self._run_git(
            ["branch", "-vv", "--format=%(refname:short)|%(objectname:short)|%(authorname)|%(committerdate:relative)"]
        )
        
        branches = []
        if code == 0:
            for line in stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 4:
                        branches.append(BranchInfo(
                            name=parts[0],
                            commit=parts[1],
                            author=parts[2],
                            last_commit_date=parts[3],
                            is_remote=False
                        ))
        return branches
    
    def get_current_branch(self) -> Optional[str]:
        """Get current branch name"""
        code, stdout, _ = self._run_git(["branch", "--show-current"])
        if code == 0:
            return stdout.strip()
        return None
    
    def commit_changes(self, message: str, 
                      files: Optional[List[str]] = None) -> bool:
        """Commit changes"""
        if files:
            self._run_git(["add"] + files)
        else:
            self._run_git(["add", "."])
        
        code, _, _ = self._run_git(["commit", "-m", message])
        return code == 0
    
    def push_branch(self, branch_name: Optional[str] = None,
                   remote: str = "origin") -> bool:
        """Push branch to remote"""
        branch = branch_name or self.get_current_branch()
        if not branch:
            return False
        
        code, _, _ = self._run_git(["push", "-u", remote, branch])
        return code == 0
    
    def merge_branch(self, branch_name: str, 
                    strategy: str = "merge") -> bool:
        """Merge branch into current"""
        if strategy == "rebase":
            code, _, _ = self._run_git(["rebase", branch_name])
        else:
            code, _, _ = self._run_git(["merge", branch_name])
        return code == 0
    
    def get_branch_diff(self, branch1: str, 
                       branch2: str = "HEAD") -> List[str]:
        """Get diff between branches"""
        code, stdout, _ = self._run_git(
            ["diff", "--name-only", f"{branch1}...{branch2}"]
        )
        if code == 0:
            return stdout.strip().split("\n") if stdout else []
        return []
    
    def stash_changes(self, message: Optional[str] = None) -> bool:
        """Stash current changes"""
        cmd = ["stash", "push"]
        if message:
            cmd.extend(["-m", message])
        code, _, _ = self._run_git(cmd)
        return code == 0
    
    def pop_stash(self) -> bool:
        """Pop stash"""
        code, _, _ = self._run_git(["stash", "pop"])
        return code == 0

# Global manager
_default_manager = GitBranchManager()

def create_agent_branch(agent_id: str) -> Optional[str]:
    """Create branch for agent"""
    return _default_manager.create_agent_branch(agent_id)

def get_current_branch() -> Optional[str]:
    """Get current branch"""
    return _default_manager.get_current_branch()
