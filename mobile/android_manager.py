import subprocess
import re
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

class AndroidDeviceManager:
    def __init__(self):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.adb_path = self._find_adb()
        
    def _find_adb(self) -> str:
        adb_paths = [
            'adb',
            '/usr/bin/adb',
            '/usr/local/bin/adb',
            os.path.expanduser('~/Android/Sdk/platform-tools/adb'),
            '/opt/android-sdk/platform-tools/adb'
        ]
        for path in adb_paths:
            try:
                result = subprocess.run([path, 'version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return path
            except:
                continue
        return 'adb'
    
    async def list_devices(self) -> Dict[str, Any]:
        try:
            result = await asyncio.create_subprocess_exec(
                self.adb_path, 'devices', '-l',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            output = stdout.decode()
            
            devices = []
            for line in output.split('\n')[1:]:
                if line.strip() and not line.startswith('*'):
                    parts = line.split()
                    if len(parts) >= 2:
                        serial = parts[0]
                        status = parts[1]
                        device_info = {"serial": serial, "status": status}
                        
                        # Get device properties
                        if status == 'device':
                            props = await self._get_device_props(serial)
                            device_info.update(props)
                        
                        devices.append(device_info)
                        self.devices[serial] = device_info
            
            return {"success": True, "devices": devices, "count": len(devices)}
        except Exception as e:
            return {"success": False, "error": str(e), "devices": []}
    
    async def _get_device_props(self, serial: str) -> Dict[str, str]:
        props = {}
        try:
            result = await asyncio.create_subprocess_exec(
                self.adb_path, '-s', serial, 'shell', 'getprop',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            output = stdout.decode()
            
            for line in output.split('\n'):
                if 'ro.product.model' in line:
                    props['model'] = line.split(':')[-1].strip()[1:-1]
                elif 'ro.product.manufacturer' in line:
                    props['manufacturer'] = line.split(':')[-1].strip()[1:-1]
                elif 'ro.build.version.release' in line:
                    props['android_version'] = line.split(':')[-1].strip()[1:-1]
        except:
            pass
        return props
    
    async def connect_device(self, serial: str) -> Dict[str, Any]:
        try:
            result = await asyncio.create_subprocess_exec(
                self.adb_path, 'connect', serial,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            output = stdout.decode()
            
            if 'connected' in output.lower() or 'already connected' in output.lower():
                self.devices[serial] = {"serial": serial, "status": "connected", "connected_at": datetime.now().isoformat()}
                return {"success": True, "serial": serial, "message": output.strip()}
            else:
                return {"success": False, "serial": serial, "error": output.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def disconnect_device(self, serial: str) -> Dict[str, Any]:
        try:
            result = await asyncio.create_subprocess_exec(
                self.adb_path, 'disconnect', serial,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if serial in self.devices:
                del self.devices[serial]
            
            return {"success": True, "serial": serial}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_shell(self, serial: str, command: str) -> Dict[str, Any]:
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
                "stderr": stderr.decode(),
                "returncode": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def install_app(self, serial: str, apk_path: str) -> Dict[str, Any]:
        try:
            result = await asyncio.create_subprocess_exec(
                self.adb_path, '-s', serial, 'install', '-r', apk_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            output = stdout.decode()
            
            success = 'success' in output.lower()
            return {"success": success, "output": output, "serial": serial}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def uninstall_app(self, serial: str, package: str) -> Dict[str, Any]:
        try:
            result = await asyncio.create_subprocess_exec(
                self.adb_path, '-s', serial, 'uninstall', package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            output = stdout.decode()
            
            success = 'success' in output.lower()
            return {"success": success, "output": output, "serial": serial}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def start_app(self, serial: str, package: str, activity: Optional[str] = None) -> Dict[str, Any]:
        try:
            if activity:
                cmd = f"am start -n {package}/{activity}"
            else:
                cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
            
            result = await self.execute_shell(serial, cmd)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def stop_app(self, serial: str, package: str) -> Dict[str, Any]:
        try:
            result = await self.execute_shell(serial, f"am force-stop {package}")
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self, serial: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not output_path:
                output_path = f"/tmp/android_screenshot_{serial.replace(':', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # Take screenshot on device
            device_path = "/sdcard/screenshot.png"
            await self.execute_shell(serial, f"screencap -p {device_path}")
            
            # Pull to local
            result = await asyncio.create_subprocess_exec(
                self.adb_path, '-s', serial, 'pull', device_path, output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            # Clean up device
            await self.execute_shell(serial, f"rm {device_path}")
            
            if os.path.exists(output_path):
                return {"success": True, "path": output_path, "serial": serial}
            else:
                return {"success": False, "error": "Screenshot file not created"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_packages(self, serial: str) -> Dict[str, Any]:
        try:
            result = await self.execute_shell(serial, "pm list packages")
            if result["success"]:
                packages = []
                for line in result["stdout"].split('\n'):
                    if 'package:' in line:
                        pkg = line.replace('package:', '').strip()
                        packages.append(pkg)
                return {"success": True, "packages": packages, "count": len(packages)}
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_screen_size(self, serial: str) -> Dict[str, Any]:
        try:
            result = await self.execute_shell(serial, "wm size")
            if result["success"]:
                match = re.search(r'(\d+)x(\d+)', result["stdout"])
                if match:
                    return {"success": True, "width": int(match.group(1)), "height": int(match.group(2))}
            return {"success": False, "error": "Could not get screen size"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def reboot(self, serial: str) -> Dict[str, Any]:
        try:
            result = await asyncio.create_subprocess_exec(
                self.adb_path, '-s', serial, 'reboot',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return {"success": result.returncode == 0, "serial": serial}
        except Exception as e:
            return {"success": False, "error": str(e)}

android_manager = AndroidDeviceManager()
