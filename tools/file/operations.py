"""
LEGIONGASPER v2.0 - File Operations Tool
OpenClaw-compatible file read/write/edit/search
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import os
import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FileResult:
    """Result of file operation"""
    success: bool
    path: str
    content: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class FileManager:
    """File operations manager with safety checks"""
    
    def __init__(self, base_path: str = ".", allow_absolute: bool = False):
        self.base_path = Path(base_path).resolve()
        self.allow_absolute = allow_absolute
        
    def _resolve_path(self, path: str) -> Path:
        """Resolve path with safety checks"""
        target = Path(path)
        if not self.allow_absolute and target.is_absolute():
            target = self.base_path / target.relative_to(target.anchor)
        return target.resolve()
    
    def read(self, path: str, encoding: str = "utf-8") -> FileResult:
        """Read file contents"""
        try:
            target = self._resolve_path(path)
            if not target.exists():
                return FileResult(False, path, error=f"File not found: {path}")
            
            content = target.read_text(encoding=encoding)
            stat = target.stat()
            
            return FileResult(
                success=True,
                path=str(target),
                content=content,
                metadata={
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                }
            )
        except Exception as e:
            return FileResult(False, path, error=str(e))
    
    def write(self, path: str, content: str, encoding: str = "utf-8") -> FileResult:
        """Write file contents"""
        try:
            target = self._resolve_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding=encoding)
            
            return FileResult(
                success=True,
                path=str(target),
                content=content
            )
        except Exception as e:
            return FileResult(False, path, error=str(e))
    
    def edit(self, path: str, 
             old_string: Optional[str] = None,
             new_string: Optional[str] = None,
             pattern: Optional[str] = None,
             replacement: Optional[str] = None) -> FileResult:
        """Edit file contents"""
        try:
            target = self._resolve_path(path)
            if not target.exists():
                return FileResult(False, path, error=f"File not found: {path}")
            
            content = target.read_text()
            
            if old_string and new_string is not None:
                if old_string not in content:
                    return FileResult(False, path, error=f"String not found: {old_string}")
                content = content.replace(old_string, new_string)
            elif pattern and replacement is not None:
                content = re.sub(pattern, replacement, content)
            else:
                return FileResult(False, path, error="Invalid edit parameters")
            
            target.write_text(content)
            
            return FileResult(
                success=True,
                path=str(target),
                content=content
            )
        except Exception as e:
            return FileResult(False, path, error=str(e))
    
    def search(self, pattern: str, path: str = ".", 
               recursive: bool = True) -> List[Dict[str, Any]]:
        """Search for files matching pattern"""
        results = []
        target = self._resolve_path(path)
        
        try:
            if recursive:
                files = target.rglob(pattern)
            else:
                files = target.glob(pattern)
            
            for file_path in files:
                if file_path.is_file():
                    stat = file_path.stat()
                    results.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        except Exception as e:
            pass
        
        return results
    
    def search_content(self, pattern: str, path: str = ".",
                     file_pattern: str = "*") -> List[Dict[str, Any]]:
        """Search for content within files"""
        results = []
        target = self._resolve_path(path)
        
        try:
            for file_path in target.rglob(file_pattern):
                if file_path.is_file():
                    try:
                        content = file_path.read_text()
                        matches = list(re.finditer(pattern, content, re.MULTILINE))
                        if matches:
                            results.append({
                                "path": str(file_path),
                                "matches": len(matches),
                                "lines": [content[max(0, m.start()-50):m.end()+50] 
                                         for m in matches[:5]]
                            })
                    except:
                        continue
        except Exception as e:
            pass
        
        return results
    
    def list_dir(self, path: str = ".") -> List[Dict[str, Any]]:
        """List directory contents"""
        results = []
        target = self._resolve_path(path)
        
        try:
            for item in target.iterdir():
                stat = item.stat()
                results.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        except Exception as e:
            pass
        
        return results

# Global file manager instance
_default_manager = FileManager()

def read(path: str, **kwargs) -> FileResult:
    """Read file"""
    return _default_manager.read(path, **kwargs)

def write(path: str, content: str, **kwargs) -> FileResult:
    """Write file"""
    return _default_manager.write(path, content, **kwargs)

def edit(path: str, **kwargs) -> FileResult:
    """Edit file"""
    return _default_manager.edit(path, **kwargs)

def search(pattern: str, **kwargs) -> List[Dict[str, Any]]:
    """Search files"""
    return _default_manager.search(pattern, **kwargs)

def search_content(pattern: str, **kwargs) -> List[Dict[str, Any]]:
    """Search file contents"""
    return _default_manager.search_content(pattern, **kwargs)
