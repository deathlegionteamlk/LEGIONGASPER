import asyncio
import random
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

class GestureEngine:
    def __init__(self):
        self.adb_path = 'adb'
        
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
    
    async def tap(self, serial: str, x: int, y: int, 
                  random_offset: int = 0) -> Dict[str, Any]:
        if random_offset > 0:
            x += random.randint(-random_offset, random_offset)
            y += random.randint(-random_offset, random_offset)
        
        return await self._execute_shell(serial, f"input tap {x} {y}")
    
    async def long_press(self, serial: str, x: int, y: int, 
                         duration_ms: int = 1000) -> Dict[str, Any]:
        return await self._execute_shell(serial, 
            f"input swipe {x} {y} {x} {y} {duration_ms}")
    
    async def swipe(self, serial: str, x1: int, y1: int, x2: int, y2: int,
                    duration_ms: int = 300) -> Dict[str, Any]:
        return await self._execute_shell(serial,
            f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
    
    async def scroll(self, serial: str, direction: str = "down",
                     distance: int = 500, duration_ms: int = 300) -> Dict[str, Any]:
        # Get screen center
        result = await self._execute_shell(serial, "wm size")
        if not result['success']:
            return result
        
        import re
        match = re.search(r'(\d+)x(\d+)', result['stdout'])
        if not match:
            return {"success": False, "error": "Could not get screen size"}
        
        width = int(match.group(1))
        height = int(match.group(2))
        center_x = width // 2
        center_y = height // 2
        
        if direction == "down":
            return await self.swipe(serial, center_x, center_y + distance//2,
                                   center_x, center_y - distance//2, duration_ms)
        elif direction == "up":
            return await self.swipe(serial, center_x, center_y - distance//2,
                                   center_x, center_y + distance//2, duration_ms)
        elif direction == "left":
            return await self.swipe(serial, center_x - distance//2, center_y,
                                   center_x + distance//2, center_y, duration_ms)
        elif direction == "right":
            return await self.swipe(serial, center_x + distance//2, center_y,
                                   center_x - distance//2, center_y, duration_ms)
        else:
            return {"success": False, "error": f"Unknown direction: {direction}"}
    
    async def pinch_zoom(self, serial: str, center_x: int, center_y: int,
                         scale: float = 2.0, duration_ms: int = 500) -> Dict[str, Any]:
        # Simulate pinch zoom using two-finger gesture
        # Android doesn't support native multi-touch via ADB, so we simulate
        distance = int(100 * scale)
        
        # First swipe outward (zoom in)
        await self.swipe(serial, center_x - distance//2, center_y,
                         center_x + distance//2, center_y, duration_ms)
        
        return {"success": True, "action": "pinch_zoom", "scale": scale}
    
    async def double_tap(self, serial: str, x: int, y: int,
                         interval_ms: int = 100) -> Dict[str, Any]:
        await self.tap(serial, x, y)
        await asyncio.sleep(interval_ms / 1000)
        return await self.tap(serial, x, y)
    
    async def drag_and_drop(self, serial: str, x1: int, y1: int,
                            x2: int, y2: int, duration_ms: int = 1000) -> Dict[str, Any]:
        # Long press at start
        await self.long_press(serial, x1, y1, 500)
        # Drag to end
        return await self.swipe(serial, x1, y1, x2, y2, duration_ms)
    
    async def fling(self, serial: str, direction: str = "down",
                    velocity: int = 1000) -> Dict[str, Any]:
        # Fast swipe for fling
        duration = max(100, 500 - velocity // 10)  # Faster = shorter duration
        return await self.scroll(serial, direction, distance=800, duration_ms=duration)
    
    async def pattern_unlock(self, serial: str, pattern: list) -> Dict[str, Any]:
        # Pattern is list of (x, y) coordinates
        if len(pattern) < 2:
            return {"success": False, "error": "Pattern needs at least 2 points"}
        
        # Build swipe command through all points
        points_str = " ".join([f"{x} {y}" for x, y in pattern])
        return await self._execute_shell(serial, f"input swipe {points_str}")
    
    async def type_text(self, serial: str, text: str) -> Dict[str, Any]:
        escaped = text.replace("'", "\\'")
        return await self._execute_shell(serial, f"input text '{escaped}'")
    
    async def press_key(self, serial: str, keycode: int) -> Dict[str, Any]:
        return await self._execute_shell(serial, f"input keyevent {keycode}")
    
    async def press_home(self, serial: str) -> Dict[str, Any]:
        return await self.press_key(serial, 3)  # KEYCODE_HOME
    
    async def press_back(self, serial: str) -> Dict[str, Any]:
        return await self.press_key(serial, 4)  # KEYCODE_BACK
    
    async def press_recent(self, serial: str) -> Dict[str, Any]:
        return await self.press_key(serial, 187)  # KEYCODE_APP_SWITCH
    
    async def press_power(self, serial: str) -> Dict[str, Any]:
        return await self.press_key(serial, 26)  # KEYCODE_POWER
    
    async def volume_up(self, serial: str) -> Dict[str, Any]:
        return await self.press_key(serial, 24)  # KEYCODE_VOLUME_UP
    
    async def volume_down(self, serial: str) -> Dict[str, Any]:
        return await self.press_key(serial, 25)  # KEYCODE_VOLUME_DOWN
    
    async def take_screenshot(self, serial: str, path: str) -> Dict[str, Any]:
        device_path = "/sdcard/screenshot.png"
        await self._execute_shell(serial, f"screencap -p {device_path}")
        
        result = await asyncio.create_subprocess_exec(
            self.adb_path, '-s', serial, 'pull', device_path, path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        await self._execute_shell(serial, f"rm {device_path}")
        
        return {"success": result.returncode == 0, "path": path}

gesture_engine = GestureEngine()
