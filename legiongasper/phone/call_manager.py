import asyncio
import re
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CallState(Enum):
    IDLE = "idle"
    RINGING = "ringing"
    OFFHOOK = "offhook"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HOLD = "hold"


class CallType(Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    MISSED = "missed"
    REJECTED = "rejected"


@dataclass
class CallRecord:
    call_id: str
    phone_number: str
    contact_name: Optional[str]
    call_type: CallType
    state: CallState
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: int
    is_recorded: bool = False
    recording_path: Optional[str] = None
    transcription: Optional[str] = None
    ai_summary: Optional[str] = None


@dataclass
class CallLog:
    calls: List[CallRecord] = field(default_factory=list)
    total_calls: int = 0
    total_duration: int = 0


class CallManager:
    def __init__(self, phone_manager):
        self.phone_manager = phone_manager
        self.current_call: Optional[CallRecord] = None
        self.call_history: List[CallRecord] = []
        self._state_callbacks: List[Callable] = []
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._auto_answer_enabled = False
        self._auto_answer_delay = 3
        self._call_screening_enabled = False
        self._blocked_numbers: set = set()
        self._allowed_contacts: set = set()

    async def start_monitoring(self):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_calls())

    async def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitor_calls(self):
        last_state = CallState.IDLE
        while self._monitoring:
            try:
                status = await self.phone_manager.get_status()
                current_state = self._parse_call_state(status.call_state)
                if current_state != last_state:
                    await self._handle_state_change(last_state, current_state, status)
                    last_state = current_state
                await asyncio.sleep(0.5)
            except Exception:
                await asyncio.sleep(1)

    def _parse_call_state(self, state_str: str) -> CallState:
        state_map = {
            "idle": CallState.IDLE,
            "ringing": CallState.RINGING,
            "offhook": CallState.OFFHOOK,
        }
        return state_map.get(state_str.lower(), CallState.IDLE)

    async def _handle_state_change(self, old_state: CallState, new_state: CallState, status):
        if new_state == CallState.RINGING and old_state == CallState.IDLE:
            await self._handle_incoming_call()
        elif new_state == CallState.OFFHOOK and old_state == CallState.RINGING:
            await self._handle_call_connected()
        elif new_state == CallState.IDLE and old_state in [CallState.OFFHOOK, CallState.RINGING]:
            await self._handle_call_ended()
        for callback in self._state_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_state, new_state, status)
                else:
                    callback(old_state, new_state, status)
            except Exception:
                pass

    async def _handle_incoming_call(self):
        try:
            result = await self.phone_manager.execute_shell_command("dumpsys telephony.registry | grep 'mCallIncomingNumber'")
            phone_number = self._extract_phone_number(result)
            if self._call_screening_enabled:
                should_answer = await self._screen_call(phone_number)
                if not should_answer:
                    await self.reject_call()
                    return
            if self._auto_answer_enabled:
                await asyncio.sleep(self._auto_answer_delay)
                if self.current_call and self.current_call.state == CallState.RINGING:
                    await self.answer_call()
        except Exception:
            pass

    async def _handle_call_connected(self):
        if self.current_call:
            self.current_call.state = CallState.CONNECTED
            self.current_call.start_time = datetime.now()

    async def _handle_call_ended(self):
        if self.current_call:
            self.current_call.end_time = datetime.now()
            if self.current_call.start_time:
                duration = (self.current_call.end_time - self.current_call.start_time).seconds
                self.current_call.duration = duration
            self.call_history.append(self.current_call)
            self.current_call = None

    async def _screen_call(self, phone_number: str) -> bool:
        if phone_number in self._blocked_numbers:
            return False
        if self._allowed_contacts and phone_number not in self._allowed_contacts:
            return False
        return True

    def _extract_phone_number(self, text: str) -> str:
        match = re.search(r'\+?[\d\s\-\(\)]{7,}', text)
        return match.group(0).strip() if match else "unknown"

    async def answer_call(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 79")
            if self.current_call:
                self.current_call.state = CallState.CONNECTED
            return True
        except Exception:
            return False

    async def reject_call(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 6")
            if self.current_call:
                self.current_call.state = CallState.DISCONNECTED
                self.current_call.call_type = CallType.REJECTED
            return True
        except Exception:
            return False

    async def end_call(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 6")
            if self.current_call:
                self.current_call.state = CallState.DISCONNECTED
            return True
        except Exception:
            return False

    async def dial_number(self, phone_number: str) -> bool:
        try:
            encoded_number = phone_number.replace(" ", "").replace("-", "")
            await self.phone_manager.execute_shell_command(f"am start -a android.intent.action.CALL -d tel:{encoded_number}")
            self.current_call = CallRecord(
                call_id=f"out_{datetime.now().timestamp()}",
                phone_number=phone_number,
                contact_name=None,
                call_type=CallType.OUTGOING,
                state=CallState.OFFHOOK,
                start_time=datetime.now(),
                end_time=None,
                duration=0,
            )
            return True
        except Exception:
            return False

    async def mute_call(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 91")
            return True
        except Exception:
            return False

    async def unmute_call(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 91")
            return True
        except Exception:
            return False

    async def hold_call(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 231")
            if self.current_call:
                self.current_call.state = CallState.HOLD
            return True
        except Exception:
            return False

    async def resume_call(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 231")
            if self.current_call:
                self.current_call.state = CallState.CONNECTED
            return True
        except Exception:
            return False

    async def send_dtmf(self, digit: str) -> bool:
        try:
            keycode_map = {
                "0": 7, "1": 8, "2": 9, "3": 10, "4": 11,
                "5": 12, "6": 13, "7": 14, "8": 15, "9": 16,
                "*": 17, "#": 18,
            }
            if digit in keycode_map:
                await self.phone_manager.execute_shell_command(f"input keyevent {keycode_map[digit]}")
            return True
        except Exception:
            return False

    async def get_call_log(self, limit: int = 100) -> CallLog:
        try:
            result = await self.phone_manager.execute_shell_command("content query --uri content://call_log/calls --projection number:name:duration:type:date --limit " + str(limit))
            calls = []
            for line in result.split("\n"):
                if "number=" in line:
                    call = self._parse_call_log_entry(line)
                    if call:
                        calls.append(call)
            return CallLog(calls=calls, total_calls=len(calls), total_duration=sum(c.duration for c in calls))
        except Exception:
            return CallLog(calls=self.call_history[-limit:], total_calls=len(self.call_history), total_duration=sum(c.duration for c in self.call_history))

    def _parse_call_log_entry(self, line: str) -> Optional[CallRecord]:
        try:
            parts = line.split(", ")
            data = {}
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    data[key.strip()] = value.strip()
            call_type = CallType.INCOMING if data.get("type") == "1" else CallType.OUTGOING if data.get("type") == "2" else CallType.MISSED
            return CallRecord(
                call_id=data.get("_id", "unknown"),
                phone_number=data.get("number", "unknown"),
                contact_name=data.get("name"),
                call_type=call_type,
                state=CallState.DISCONNECTED,
                start_time=None,
                end_time=None,
                duration=int(data.get("duration", 0)),
            )
        except Exception:
            return None

    async def start_recording(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 252")
            if self.current_call:
                self.current_call.is_recorded = True
            return True
        except Exception:
            return False

    async def stop_recording(self) -> bool:
        try:
            await self.phone_manager.execute_shell_command("input keyevent 252")
            return True
        except Exception:
            return False

    def register_state_callback(self, callback: Callable):
        self._state_callbacks.append(callback)

    def unregister_state_callback(self, callback: Callable):
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def enable_auto_answer(self, delay_seconds: int = 3):
        self._auto_answer_enabled = True
        self._auto_answer_delay = delay_seconds

    def disable_auto_answer(self):
        self._auto_answer_enabled = False

    def enable_call_screening(self):
        self._call_screening_enabled = True

    def disable_call_screening(self):
        self._call_screening_enabled = False

    def block_number(self, phone_number: str):
        self._blocked_numbers.add(phone_number)

    def unblock_number(self, phone_number: str):
        self._blocked_numbers.discard(phone_number)

    def allow_contact(self, phone_number: str):
        self._allowed_contacts.add(phone_number)

    def remove_allowed_contact(self, phone_number: str):
        self._allowed_contacts.discard(phone_number)

    async def get_current_call(self) -> Optional[CallRecord]:
        return self.current_call

    async def get_call_history(self, limit: int = 50) -> List[CallRecord]:
        return self.call_history[-limit:]
