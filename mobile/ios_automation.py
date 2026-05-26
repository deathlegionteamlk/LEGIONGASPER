import subprocess
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

try:
    from pymobiledevice3 import usbmux
    from pymobiledevice3.lockdown import LockdownClient
    IOS_AVAILABLE = True
except ImportError:
    IOS_AVAILABLE = False

class IOSDeviceManager:
    def __init__(self):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.available = IOS_AVAILABLE
        
    async def list_devices(self) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed", "devices": []}
        
        try:
            # Use usbmux to list connected devices
            devices = []
            try:
                from pymobiledevice3.usbmux import list_devices
                for device in list_devices():
                    device_info = {
                        "udid": device.serial,
                        "connection_type": device.connection_type,
                        "status": "connected"
                    }
                    
                    # Try to get more info via lockdown
                    try:
                        lockdown = LockdownClient(device.serial)
                        device_info.update({
                            "name": lockdown.get_device_name(),
                            "ios_version": lockdown.ios_version,
                            "model": lockdown.get_model(),
                            "battery": lockdown.get_battery_level()
                        })
                    except:
                        pass
                    
                    devices.append(device_info)
                    self.devices[device.serial] = device_info
            except Exception as e:
                return {"success": False, "error": str(e), "devices": []}
            
            return {"success": True, "devices": devices, "count": len(devices)}
        except Exception as e:
            return {"success": False, "error": str(e), "devices": []}
    
    async def connect_device(self, udid: str) -> Dict[str, Any]:
        try:
            lockdown = LockdownClient(udid)
            self.devices[udid] = {
                "udid": udid,
                "name": lockdown.get_device_name(),
                "status": "connected",
                "connected_at": datetime.now().isoformat()
            }
            return {"success": True, "udid": udid, "name": lockdown.get_device_name()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def install_app(self, udid: str, ipa_path: str) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed"}
        
        try:
            from pymobiledevice3.services.installation_proxy import InstallationProxyService
            lockdown = LockdownClient(udid)
            installation_proxy = InstallationProxyService(lockdown)
            installation_proxy.install(ipa_path)
            return {"success": True, "udid": udid, "ipa": ipa_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def launch_app(self, udid: str, bundle_id: str) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed"}
        
        try:
            from pymobiledevice3.services.springboard import SpringBoardServicesService
            lockdown = LockdownClient(udid)
            springboard = SpringBoardServicesService(lockdown)
            springboard.launch(bundle_id)
            return {"success": True, "udid": udid, "bundle_id": bundle_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def terminate_app(self, udid: str, bundle_id: str) -> Dict[str, Any]:
        try:
            # Use XCTest or instruments to terminate
            result = await self._run_instruments(udid, f"terminate {bundle_id}")
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def press_home(self, udid: str) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed"}
        
        try:
            from pymobiledevice3.services.hid import Hid
            lockdown = LockdownClient(udid)
            hid = Hid(lockdown)
            hid.press_home()
            return {"success": True, "udid": udid, "action": "home"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def take_screenshot(self, udid: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed"}
        
        try:
            if not output_path:
                output_path = f"/tmp/ios_screenshot_{udid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            from pymobiledevice3.services.dvt import DvtSecureSocketProxyService
            lockdown = LockdownClient(udid)
            
            with DvtSecureSocketProxyService(lockdown) as dvt:
                screenshot = dvt.screenshot()
                with open(output_path, 'wb') as f:
                    f.write(screenshot)
            
            return {"success": True, "path": output_path, "udid": udid}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def simulate_touch(self, udid: str, x: int, y: int, duration: float = 0.1) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed"}
        
        try:
            from pymobiledevice3.services.hid import Hid
            lockdown = LockdownClient(udid)
            hid = Hid(lockdown)
            hid.click(x, y)
            return {"success": True, "udid": udid, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def simulate_swipe(self, udid: str, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed"}
        
        try:
            from pymobiledevice3.services.hid import Hid
            lockdown = LockdownClient(udid)
            hid = Hid(lockdown)
            hid.swipe(x1, y1, x2, y2, duration)
            return {"success": True, "udid": udid, "from": (x1, y1), "to": (x2, y2)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_installed_apps(self, udid: str) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed"}
        
        try:
            from pymobiledevice3.services.installation_proxy import InstallationProxyService
            lockdown = LockdownClient(udid)
            installation_proxy = InstallationProxyService(lockdown)
            apps = installation_proxy.get_apps()
            return {"success": True, "apps": apps, "count": len(apps)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_device_info(self, udid: str) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "pymobiledevice3 not installed"}
        
        try:
            lockdown = LockdownClient(udid)
            info = {
                "name": lockdown.get_device_name(),
                "ios_version": lockdown.ios_version,
                "model": lockdown.get_model(),
                "udid": udid,
                "battery_level": lockdown.get_battery_level(),
                "wifi_address": lockdown.get_wifi_address(),
                "phone_number": lockdown.get_phone_number()
            }
            return {"success": True, "info": info}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_instruments(self, udid: str, command: str) -> Dict[str, Any]:
        try:
            # Fallback using xcrun instruments
            result = await asyncio.create_subprocess_exec(
                'xcrun', 'instruments', '-w', udid, '-D', '/tmp/trace',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return {"success": result.returncode == 0, "stdout": stdout.decode()}
        except Exception as e:
            return {"success": False, "error": str(e)}

ios_manager = IOSDeviceManager()
