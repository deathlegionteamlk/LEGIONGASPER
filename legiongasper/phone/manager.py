import asyncio
import subprocess
import json
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp


@dataclass
class DeviceInfo:
    device_id: str
    model: str
    brand: str
    android_version: str
    battery_level: int
    is_connected: bool
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class PhoneStatus:
    is_connected: bool
    device_info: Optional[DeviceInfo]
    call_state: str
    signal_strength: int
    network_type: str
    battery_level: int


class PhoneManager:
    def __init__(self):
        self.devices: Dict[str, DeviceInfo] = {}
        self.adb_path = self._find_adb()
        self.connected_device: Optional[str] = None
        self._lock = asyncio.Lock()
        self._callbacks: List[callable] = []

    def _find_adb(self) -> str:
        adb_paths = [
            "/usr/bin/adb",
            "/usr/local/bin/adb",
            "/opt/android-sdk/platform-tools/adb",
            os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
            os.path.expanduser("~/.android-sdk/platform-tools/adb"),
        ]
        for path in adb_paths:
            if os.path.exists(path):
                return path
        return "adb"

    async def connect_device(self, device_id: Optional[str] = None) -> bool:
        async with self._lock:
            try:
                if device_id:
                    result = await self._run_adb(["-s", device_id, "shell", "echo", "connected"])
                    if "connected" in result:
                        self.connected_device = device_id
                        await self._update_device_info(device_id)
                        return True
                else:
                    devices = await self.list_devices()
                    if devices:
                        self.connected_device = devices[0]
                        await self._update_device_info(devices[0])
                        return True
                return False
            except Exception:
                return False

    async def disconnect_device(self) -> bool:
        async with self._lock:
            self.connected_device = None
            return True

    async def list_devices(self) -> List[str]:
        try:
            result = await self._run_adb(["devices"])
            lines = result.strip().split("\n")[1:]
            devices = []
            for line in lines:
                if "device" in line and not line.startswith("*"):
                    device_id = line.split()[0]
                    devices.append(device_id)
            return devices
        except Exception:
            return []

    async def _update_device_info(self, device_id: str):
        try:
            model = await self._run_adb(["-s", device_id, "shell", "getprop", "ro.product.model"])
            brand = await self._run_adb(["-s", device_id, "shell", "getprop", "ro.product.brand"])
            version = await self._run_adb(["-s", device_id, "shell", "getprop", "ro.build.version.release"])
            battery = await self._run_adb(["-s", device_id, "shell", "dumpsys", "battery"])
            battery_level = 0
            for line in battery.split("\n"):
                if "level:" in line:
                    battery_level = int(line.split(":")[1].strip())
                    break
            device_info = DeviceInfo(
                device_id=device_id,
                model=model.strip(),
                brand=brand.strip(),
                android_version=version.strip(),
                battery_level=battery_level,
                is_connected=True,
            )
            self.devices[device_id] = device_info
        except Exception:
            pass

    async def get_status(self) -> PhoneStatus:
        async with self._lock:
            if not self.connected_device:
                return PhoneStatus(
                    is_connected=False,
                    device_info=None,
                    call_state="unknown",
                    signal_strength=0,
                    network_type="none",
                    battery_level=0,
                )
            device_info = self.devices.get(self.connected_device)
            try:
                telephony = await self._run_adb(["-s", self.connected_device, "shell", "dumpsys", "telephony.registry"])
                call_state = "idle"
                signal_strength = 0
                network_type = "unknown"
                for line in telephony.split("\n"):
                    if "mCallState" in line:
                        state = line.split("=")[-1].strip()
                        if state == "1":
                            call_state = "ringing"
                        elif state == "2":
                            call_state = "offhook"
                    if "SignalStrength" in line and "gsm" in line.lower():
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit() and len(part) <= 2:
                                signal_strength = int(part)
                                break
                return PhoneStatus(
                    is_connected=True,
                    device_info=device_info,
                    call_state=call_state,
                    signal_strength=signal_strength,
                    network_type=network_type,
                    battery_level=device_info.battery_level if device_info else 0,
                )
            except Exception:
                return PhoneStatus(
                    is_connected=True,
                    device_info=device_info,
                    call_state="unknown",
                    signal_strength=0,
                    network_type="unknown",
                    battery_level=device_info.battery_level if device_info else 0,
                )

    async def _run_adb(self, args: List[str]) -> str:
        cmd = [self.adb_path] + args
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"ADB error: {stderr.decode()}")
        return stdout.decode()

    async def execute_shell_command(self, command: str) -> str:
        if not self.connected_device:
            raise Exception("No device connected")
        return await self._run_adb(["-s", self.connected_device, "shell", command])

    async def install_app(self, apk_path: str) -> bool:
        if not self.connected_device:
            raise Exception("No device connected")
        try:
            await self._run_adb(["-s", self.connected_device, "install", "-r", apk_path])
            return True
        except Exception:
            return False

    async def uninstall_app(self, package_name: str) -> bool:
        if not self.connected_device:
            raise Exception("No device connected")
        try:
            await self._run_adb(["-s", self.connected_device, "uninstall", package_name])
            return True
        except Exception:
            return False

    async def start_app(self, package_name: str, activity: Optional[str] = None) -> bool:
        if not self.connected_device:
            raise Exception("No device connected")
        try:
            if activity:
                await self._run_adb(["-s", self.connected_device, "shell", "am", "start", "-n", f"{package_name}/{activity}"])
            else:
                await self._run_adb(["-s", self.connected_device, "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"])
            return True
        except Exception:
            return False

    async def stop_app(self, package_name: str) -> bool:
        if not self.connected_device:
            raise Exception("No device connected")
        try:
            await self._run_adb(["-s", self.connected_device, "shell", "am", "force-stop", package_name])
            return True
        except Exception:
            return False

    async def take_screenshot(self) -> bytes:
        if not self.connected_device:
            raise Exception("No device connected")
        try:
            await self._run_adb(["-s", self.connected_device, "shell", "screencap", "/sdcard/screenshot.png"])
            await self._run_adb(["-s", self.connected_device, "pull", "/sdcard/screenshot.png", "/tmp/screenshot.png"])
            with open("/tmp/screenshot.png", "rb") as f:
                return f.read()
        except Exception:
            return b""

    def register_callback(self, callback: callable):
        self._callbacks.append(callback)

    async def _notify_callbacks(self, event: str, data: Any):
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event, data)
                else:
                    callback(event, data)
            except Exception:
                pass
