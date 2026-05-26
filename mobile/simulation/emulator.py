"""
LEGIONGASPER v2.0 - Mobile Node Simulation
iOS/Android simulation for mobile agents
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random

class MobileOS(Enum):
    IOS = "ios"
    ANDROID = "android"

class DeviceType(Enum):
    PHONE = "phone"
    TABLET = "tablet"
    EMULATOR = "emulator"

@dataclass
class MobileDevice:
    """Mobile device configuration"""
    id: str
    name: str
    os: MobileOS
    os_version: str
    device_type: DeviceType
    screen_width: int
    screen_height: int
    user_agent: str
    capabilities: List[str] = field(default_factory=list)
    installed_apps: List[str] = field(default_factory=list)
    is_connected: bool = False
    battery_level: int = 100

class MobileEmulator:
    """iOS/Android mobile emulator"""
    
    IOS_USER_AGENTS = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15"
    ]
    
    ANDROID_USER_AGENTS = [
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36",
        "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36"
    ]
    
    def __init__(self):
        self.devices: Dict[str, MobileDevice] = {}
        self._device_counter = 0
        
    def create_device(self, name: str, os_type: MobileOS,
                     device_type: DeviceType = DeviceType.PHONE,
                     os_version: Optional[str] = None) -> MobileDevice:
        """Create new mobile device"""
        self._device_counter += 1
        device_id = f"mobile_{self._device_counter}"
        
        if os_type == MobileOS.IOS:
            os_version = os_version or "17.0"
            user_agent = random.choice(self.IOS_USER_AGENTS)
            screen = (390, 844) if device_type == DeviceType.PHONE else (1024, 1366)
            capabilities = ["camera", "gps", "touch", "face_id", "siri"]
            apps = ["Safari", "Messages", "Mail", "Photos", "Settings"]
        else:
            os_version = os_version or "14.0"
            user_agent = random.choice(self.ANDROID_USER_AGENTS)
            screen = (412, 915) if device_type == DeviceType.PHONE else (1600, 2560)
            capabilities = ["camera", "gps", "touch", "fingerprint", "assistant"]
            apps = ["Chrome", "Messages", "Gmail", "Photos", "Settings"]
        
        device = MobileDevice(
            id=device_id,
            name=name,
            os=os_type,
            os_version=os_version,
            device_type=device_type,
            screen_width=screen[0],
            screen_height=screen[1],
            user_agent=user_agent,
            capabilities=capabilities,
            installed_apps=apps,
            is_connected=True,
            battery_level=100
        )
        
        self.devices[device_id] = device
        return device
    
    def get_device(self, device_id: str) -> Optional[MobileDevice]:
        """Get device by ID"""
        return self.devices.get(device_id)
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List all devices"""
        return [
            {
                "id": d.id,
                "name": d.name,
                "os": d.os.value,
                "os_version": d.os_version,
                "type": d.device_type.value,
                "screen": f"{d.screen_width}x{d.screen_height}",
                "connected": d.is_connected,
                "battery": d.battery_level
            }
            for d in self.devices.values()
        ]
    
    def simulate_tap(self, device_id: str, x: int, y: int) -> bool:
        """Simulate tap on screen"""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        if 0 <= x <= device.screen_width and 0 <= y <= device.screen_height:
            return True
        return False
    
    def simulate_swipe(self, device_id: str, 
                      start_x: int, start_y: int,
                      end_x: int, end_y: int) -> bool:
        """Simulate swipe gesture"""
        device = self.devices.get(device_id)
        if not device:
            return False
        return True
    
    def simulate_text_input(self, device_id: str, 
                           text: str) -> Dict[str, Any]:
        """Simulate text input"""
        device = self.devices.get(device_id)
        if not device:
            return {"success": False, "error": "Device not found"}
        
        return {
            "success": True,
            "text_entered": text,
            "device": device_id,
            "timestamp": datetime.now().isoformat()
        }
    
    def launch_app(self, device_id: str, app_name: str) -> bool:
        """Launch app on device"""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        return app_name in device.installed_apps
    
    def take_screenshot(self, device_id: str) -> Dict[str, Any]:
        """Take screenshot"""
        device = self.devices.get(device_id)
        if not device:
            return {"success": False, "error": "Device not found"}
        
        return {
            "success": True,
            "device_id": device_id,
            "resolution": f"{device.screen_width}x{device.screen_height}",
            "format": "png",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_device_logs(self, device_id: str, 
                       lines: int = 100) -> List[str]:
        """Get device logs"""
        device = self.devices.get(device_id)
        if not device:
            return []
        
        # Simulated logs
        return [
            f"[{datetime.now().isoformat()}] Device {device_id} log entry {i}"
            for i in range(lines)
        ]
    
    def disconnect_device(self, device_id: str) -> bool:
        """Disconnect device"""
        device = self.devices.get(device_id)
        if device:
            device.is_connected = False
            return True
        return False
    
    def remove_device(self, device_id: str) -> bool:
        """Remove device"""
        if device_id in self.devices:
            del self.devices[device_id]
            return True
        return False

# Global emulator
_default_emulator = MobileEmulator()

def create_device(name: str, os_type: str, **kwargs) -> MobileDevice:
    """Create mobile device"""
    os_enum = MobileOS.IOS if os_type.lower() == "ios" else MobileOS.ANDROID
    return _default_emulator.create_device(name, os_enum, **kwargs)

def list_devices() -> List[Dict[str, Any]]:
    """List devices"""
    return _default_emulator.list_devices()
