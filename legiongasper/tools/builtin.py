import asyncio
import json
import re
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import urlparse

from .registry import ToolRegistry, ToolSchema, ToolPermission, ToolParameter

async def web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    
    return {
        "query": query,
        "results": [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result{i}",
                "snippet": f"This is a placeholder result for query: {query}"
            }
            for i in range(min(num_results, 5))
        ]
    }

async def web_scrape(url: str, extract_text: bool = True) -> Dict[str, Any]:
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                content = await response.text()
                
                if extract_text:
                    
                    text = re.sub('<[^<]+?>', '', content)
                    text = re.sub('\s+', ' ', text).strip()
                    content = text[:5000]  
                
                return {
                    "url": url,
                    "status": response.status,
                    "content": content[:10000],  
                    "content_type": response.headers.get('content-type', 'unknown')
                }
    except Exception as e:
        return {
            "url": url,
            "error": str(e)
        }

async def code_execution(code: str, 
                        language: str = "python",
                        timeout: int = 30) -> Dict[str, Any]:
    
    if language != "python":
        return {
            "success": False,
            "error": f"Language {language} not supported"
        }
    
    try:
        
        safe_globals = {
            "__builtins__": {
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "print": lambda *args: " ".join(str(a) for a in args),
                "True": True,
                "False": False,
                "None": None,
            }
        }
        
        loop = asyncio.get_event_loop()
        
        def run_code():
            exec(code, safe_globals, {})
            return safe_globals.get("_result", "Code executed successfully")
        
        result = await asyncio.wait_for(
            loop.run_in_executor(None, run_code),
            timeout=timeout
        )
        
        return {
            "success": True,
            "result": result,
            "language": language
        }
        
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": f"Code execution timed out after {timeout}s"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "language": language
        }

async def file_operations(operation: str,
                         path: str,
                         content: Optional[str] = None) -> Dict[str, Any]:
    
    try:
        
        safe_base = Path("/tmp/legiongasper_files")
        safe_base.mkdir(parents=True, exist_ok=True)
        
        target_path = safe_base / path.replace("..", "").lstrip("/")
        
        if operation == "read":
            if not target_path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(target_path, 'r') as f:
                return {
                    "success": True,
                    "content": f.read(),
                    "path": str(target_path)
                }
        
        elif operation == "write":
            if content is None:
                return {"success": False, "error": "Content required for write"}
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(target_path),
                "bytes_written": len(content)
            }
        
        elif operation == "append":
            if content is None:
                return {"success": False, "error": "Content required for append"}
            
            with open(target_path, 'a') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(target_path)
            }
        
        elif operation == "delete":
            if not target_path.exists():
                return {"success": False, "error": "File not found"}
            
            target_path.unlink()
            return {"success": True, "path": str(target_path)}
        
        elif operation == "list":
            if target_path.is_dir():
                items = [
                    {"name": item.name, "type": "directory" if item.is_dir() else "file"}
                    for item in target_path.iterdir()
                ]
                return {"success": True, "items": items, "path": str(target_path)}
            else:
                return {"success": False, "error": "Not a directory"}
        
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

async def calculator(expression: str) -> Dict[str, Any]:
    
    try:
        
        allowed_names = {
            "abs": abs,
            "round": round,
            "max": max,
            "min": min,
            "sum": sum,
            "pow": pow,
        }
        
        if not re.match(r'^[\d\+\-\*\/\(\)\.\s\%]+$', expression):
            return {
                "success": False,
                "error": "Invalid characters in expression"
            }
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        
        return {
            "success": True,
            "expression": expression,
            "result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_builtin_tools() -> List[tuple]:
    
    tools = [
        (
            ToolSchema(
                name="web_search",
                description="Search the web for information",
                parameters=[
                    ToolParameter(name="query", type="string", description="Search query", required=True),
                    ToolParameter(name="num_results", type="integer", description="Number of results", required=False, default=5)
                ],
                permission=ToolPermission.PUBLIC,
                tags=["web", "search"]
            ),
            web_search
        ),
        (
            ToolSchema(
                name="web_scrape",
                description="Scrape content from a URL",
                parameters=[
                    ToolParameter(name="url", type="string", description="URL to scrape", required=True),
                    ToolParameter(name="extract_text", type="boolean", description="Extract text only", required=False, default=True)
                ],
                permission=ToolPermission.PUBLIC,
                tags=["web", "scrape"]
            ),
            web_scrape
        ),
        (
            ToolSchema(
                name="code_execution",
                description="Execute code in sandboxed environment",
                parameters=[
                    ToolParameter(name="code", type="string", description="Code to execute", required=True),
                    ToolParameter(name="language", type="string", description="Programming language", required=False, default="python", enum=["python"]),
                    ToolParameter(name="timeout", type="integer", description="Timeout in seconds", required=False, default=30)
                ],
                permission=ToolPermission.RESTRICTED,
                timeout_seconds=35,
                tags=["code", "execution"]
            ),
            code_execution
        ),
        (
            ToolSchema(
                name="file_operations",
                description="Perform file operations",
                parameters=[
                    ToolParameter(name="operation", type="string", description="Operation type", required=True, enum=["read", "write", "append", "delete", "list"]),
                    ToolParameter(name="path", type="string", description="File path", required=True),
                    ToolParameter(name="content", type="string", description="Content for write/append", required=False)
                ],
                permission=ToolPermission.RESTRICTED,
                tags=["file", "io"]
            ),
            file_operations
        ),
        (
            ToolSchema(
                name="calculator",
                description="Evaluate mathematical expressions",
                parameters=[
                    ToolParameter(name="expression", type="string", description="Math expression", required=True)
                ],
                permission=ToolPermission.PUBLIC,
                tags=["math", "calculation"]
            ),
            calculator
        ),
    ]
    
    return tools

def register_builtin_tools(registry: ToolRegistry):
    
    for schema, func in get_builtin_tools():
        registry.register(schema, func)