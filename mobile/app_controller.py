import subprocess
import xml.etree.ElementTree as ET
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
import os

class AppController:
    def __init__(self):
        self.adb_path = self._find_adb()
        self.current_package = None
        self.ui_hierarchy = None
        
    def _find_adb(self) -> str:
        adb_paths = ['adb', '/usr/bin/adb', '/usr/local/bin/adb',
                     os.path.expanduser('~/Android/Sdk/platform-tools/adb')]
        for path in adb_paths:
            try:
                result = subprocess.run([path, 'version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return path
            except:
                continue
        return 'adb'
    
    async def launch_app(self, serial: str, package: str, activity: Optional[str] = None) -> Dict[str, Any]:
        try:
            if activity:
                cmd = f"am start -n {package}/{activity}"
            else:
                cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
            
            result = await self._execute_shell(serial, cmd)
            if result['success']:
                self.current_package = package
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close_app(self, serial: str, package: str) -> Dict[str, Any]:
        try:
            return await self._execute_shell(serial, f"am force-stop {package}")
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_ui_hierarchy(self, serial: str) -> Dict[str, Any]:
        try:
            # Dump UI hierarchy
            await self._execute_shell(serial, "uiautomator dump /sdcard/window_dump.xml")
            
            # Pull to local
            local_path = f"/tmp/ui_dump_{serial.replace(':', '_')}.xml"
            await self._execute_adb(serial, ['pull', '/sdcard/window_dump.xml', local_path])
            
            # Parse XML
            if os.path.exists(local_path):
                with open(local_path, 'r') as f:
                    content = f.read()
                self.ui_hierarchy = content
                
                # Parse elements
                elements = self._parse_ui_elements(content)
                return {"success": True, "elements": elements, "xml": content}
            else:
                return {"success": False, "error": "Failed to get UI dump"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_ui_elements(self, xml_content: str) -> List[Dict[str, Any]]:
        elements = []
        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                elem = {
                    "class": node.get('class', ''),
                    "text": node.get('text', ''),
                    "resource-id": node.get('resource-id', ''),
                    "content-desc": node.get('content-desc', ''),
                    "bounds": node.get('bounds', ''),
                    "clickable": node.get('clickable', 'false') == 'true',
                    "enabled": node.get('enabled', 'false') == 'true'
                }
                if elem['text'] or elem['resource-id']:
                    elements.append(elem)
        except:
            pass
        return elements
    
    async def find_element_by_text(self, serial: str, text: str) -> Dict[str, Any]:
        result = await self.get_ui_hierarchy(serial)
        if not result['success']:
            return result
        
        for elem in result['elements']:
            if text.lower() in elem.get('text', '').lower():
                bounds = self._parse_bounds(elem['bounds'])
                return {"success": True, "element": elem, "bounds": bounds}
        
        return {"success": False, "error": f"Element with text '{text}' not found"}
    
    async def find_element_by_id(self, serial: str, resource_id: str) -> Dict[str, Any]:
        result = await self.get_ui_hierarchy(serial)
        if not result['success']:
            return result
        
        for elem in result['elements']:
            if resource_id in elem.get('resource-id', ''):
                bounds = self._parse_bounds(elem['bounds'])
                return {"success": True, "element": elem, "bounds": bounds}
        
        return {"success": False, "error": f"Element with id '{resource_id}' not found"}
    
    def _parse_bounds(self, bounds_str: str) -> Tuple[int, int, int, int]:
        # Parse "[x1,y1][x2,y2]" format
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            return (int(match.group(1)), int(match.group(2)), 
                    int(match.group(3)), int(match.group(4)))
        return (0, 0, 0, 0)
    
    def _get_center(self, bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
        return ((bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2)
    
    async def tap_element(self, serial: str, text: Optional[str] = None, 
                         resource_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            if text:
                result = await self.find_element_by_text(serial, text)
            elif resource_id:
                result = await self.find_element_by_id(serial, resource_id)
            else:
                return {"success": False, "error": "Must provide text or resource_id"}
            
            if not result['success']:
                return result
            
            center = self._get_center(result['bounds'])
            return await self.tap(serial, center[0], center[1])
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def tap(self, serial: str, x: int, y: int) -> Dict[str, Any]:
        return await self._execute_shell(serial, f"input tap {x} {y}")
    
    async def input_text(self, serial: str, text: str) -> Dict[str, Any]:
        # Escape special characters
        escaped = text.replace("'", "\\'").replace('"', '\\"')
        return await self._execute_shell(serial, f"input text '{escaped}'")
    
    async def press_key(self, serial: str, keycode: int) -> Dict[str, Any]:
        return await self._execute_shell(serial, f"input keyevent {keycode}")
    
    async def swipe(self, serial: str, x1: int, y1: int, x2: int, y2: int, 
                    duration: int = 300) -> Dict[str, Any]:
        return await self._execute_shell(serial, 
            f"input swipe {x1} {y1} {x2} {y2} {duration}")
    
    async def scroll(self, serial: str, direction: str = "down", 
                     percent: int = 80) -> Dict[str, Any]:
        # Get screen size
        size_result = await self._execute_shell(serial, "wm size")
        if not size_result['success']:
            return size_result
        
        match = re.search(r'(\d+)x(\d+)', size_result['stdout'])
        if not match:
            return {"success": False, "error": "Could not get screen size"}
        
        width = int(match.group(1))
        height = int(match.group(2))
        
        center_x = width // 2
        start_y = int(height * 0.8)
        end_y = int(height * 0.2)
        
        if direction == "down":
            return await self.swipe(serial, center_x, start_y, center_x, end_y)
        elif direction == "up":
            return await self.swipe(serial, center_x, end_y, center_x, start_y)
        else:
            return {"success": False, "error": f"Unknown direction: {direction}"}
    
    async def long_press(self, serial: str, x: int, y: int, 
                         duration: int = 1000) -> Dict[str, Any]:
        return await self._execute_shell(serial, 
            f"input swipe {x} {y} {x} {y} {duration}")
    
    async def get_current_package(self, serial: str) -> Dict[str, Any]:
        result = await self._execute_shell(serial, 
            "dumpsys window | grep mCurrentFocus")
        if result['success']:
            match = re.search(r'(\S+)/(\S+)', result['stdout'])
            if match:
                return {"success": True, "package": match.group(1), 
                        "activity": match.group(2)}
        return {"success": False, "error": "Could not get current package"}
    
    async def wait_for_element(self, serial: str, text: str, 
                                timeout: int = 10) -> Dict[str, Any]:
        start = datetime.now()
        while (datetime.now() - start).seconds < timeout:
            result = await self.find_element_by_text(serial, text)
            if result['success']:
                return result
            await asyncio.sleep(0.5)
        return {"success": False, "error": f"Timeout waiting for element: {text}"}
    
    async def _execute_shell(self, serial: str, command: str) -> Dict[str, Any]:
        try:
            result = await asyncio.create_subprocess_exec(
                self.adb_path, '-s', serial, 'shell', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return {
                "success": result.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_adb(self, serial: str, args: List[str]) -> Dict[str, Any]:
        try:
            cmd = [self.adb_path, '-s', serial] + args
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return {
                "success": result.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

app_controller = AppController()
