import asyncio
import json
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .manager import PhoneManager
from .call_manager import CallManager, CallRecord, CallState
from .sms_manager import SMSManager, SMSMessage
from .voice_controller import VoiceController


class AIAction(Enum):
    ANSWER_CALL = "answer_call"
    REJECT_CALL = "reject_call"
    SCREEN_CALL = "screen_call"
    AUTO_REPLY_SMS = "auto_reply_sms"
    TRANSCRIBE_VOICEMAIL = "transcribe_voicemail"
    PRIORITY_ESCALATE = "priority_escalate"
    DO_NOT_DISTURB = "do_not_disturb"


@dataclass
class AIContext:
    caller_history: List[Dict[str, Any]]
    time_of_day: str
    user_availability: str
    urgency_score: float
    relationship_score: float


@dataclass
class AIActionResult:
    action: AIAction
    confidence: float
    reasoning: str
    executed_at: datetime
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContactProfile:
    phone_number: str
    name: Optional[str]
    relationship: str
    priority: int
    last_interaction: Optional[datetime]
    interaction_count: int
    preferred_contact_method: str
    notes: List[str] = field(default_factory=list)


class PGOneManager:
    def __init__(self, phone_manager: PhoneManager, llm_router=None):
        self.phone_manager = phone_manager
        self.call_manager = CallManager(phone_manager)
        self.sms_manager = SMSManager(phone_manager, llm_router)
        self.voice_controller = VoiceController(phone_manager)
        self.llm_router = llm_router
        self._contacts: Dict[str, ContactProfile] = {}
        self._action_history: List[AIActionResult] = []
        self._callbacks: List[Callable] = []
        self._active = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._ai_personality = "professional"
        self._do_not_disturb = False
        self._dnd_exceptions: set = set()
        self._auto_transcribe = True
        self._smart_screening = True

    async def initialize(self):
        await self.call_manager.start_monitoring()
        await self.sms_manager.start_monitoring()
        await self.voice_controller.initialize()
        self._active = True
        self._monitor_task = asyncio.create_task(self._ai_monitor_loop())

    async def shutdown(self):
        self._active = False
        await self.call_manager.stop_monitoring()
        await self.sms_manager.stop_monitoring()
        await self.voice_controller.stop_listening()
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _ai_monitor_loop(self):
        while self._active:
            try:
                await self._process_pending_actions()
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(2)

    async def _process_pending_actions(self):
        current_call = await self.call_manager.get_current_call()
        if current_call and current_call.state == CallState.RINGING:
            await self._handle_incoming_call_ai(current_call)

    async def _handle_incoming_call_ai(self, call: CallRecord):
        if self._do_not_disturb:
            if call.phone_number not in self._dnd_exceptions:
                await self.call_manager.reject_call()
                return
        contact = self._get_or_create_contact(call.phone_number)
        context = await self._build_ai_context(contact, call)
        action, confidence, reasoning = await self._decide_call_action(call, contact, context)
        result = AIActionResult(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            executed_at=datetime.now(),
            success=False,
        )
        if action == AIAction.ANSWER_CALL:
            result.success = await self.call_manager.answer_call()
            if result.success and self._auto_transcribe:
                await self._start_call_transcription(call)
        elif action == AIAction.REJECT_CALL:
            result.success = await self.call_manager.reject_call()
        elif action == AIAction.SCREEN_CALL:
            result.success = await self._screen_call_with_ai(call, contact)
        self._action_history.append(result)
        await self._notify_callbacks("call_handled", result)

    async def _build_ai_context(self, contact: ContactProfile, call: CallRecord) -> AIContext:
        hour = datetime.now().hour
        time_of_day = "morning" if 6 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening" if 18 <= hour < 22 else "night"
        user_availability = "available"
        if self._do_not_disturb:
            user_availability = "do_not_disturb"
        elif hour < 8 or hour > 22:
            user_availability = "sleeping"
        urgency = 0.5
        if contact.relationship == "family":
            urgency = 0.9
        elif contact.relationship == "work":
            urgency = 0.7 if 9 <= hour < 18 else 0.4
        relationship = min(1.0, contact.interaction_count / 20)
        return AIContext(
            caller_history=[],
            time_of_day=time_of_day,
            user_availability=user_availability,
            urgency_score=urgency,
            relationship_score=relationship,
        )

    async def _decide_call_action(self, call: CallRecord, contact: ContactProfile, context: AIContext) -> tuple:
        if not self.llm_router:
            return AIAction.ANSWER_CALL, 0.5, "Default action - no LLM available"
        prompt = f"""You are HJIM (High-level Judgment and Intelligence Module), an AI phone assistant.
Decide how to handle this incoming call:

Caller: {contact.name or call.phone_number}
Relationship: {contact.relationship}
Time: {context.time_of_day}
User availability: {context.user_availability}
Urgency score: {context.urgency_score}
Relationship score: {context.relationship_score}

Options:
1. ANSWER_CALL - Answer immediately
2. REJECT_CALL - Send to voicemail
3. SCREEN_CALL - Ask caller purpose first

Respond with JSON: {{"action": "ANSWER_CALL|REJECT_CALL|SCREEN_CALL", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""
        try:
            response = await self.llm_router.generate(prompt, model_tier="nano")
            data = json.loads(response.strip())
            action = AIAction[data.get("action", "SCREEN_CALL")]
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "AI decision")
            return action, confidence, reasoning
        except Exception:
            return AIAction.ANSWER_CALL, 0.5, "Fallback due to error"

    async def _screen_call_with_ai(self, call: CallRecord, contact: ContactProfile) -> bool:
        try:
            await self.call_manager.answer_call()
            greeting = f"Hello, this is an AI assistant. {contact.name or 'The person you called'} is currently unavailable. May I ask who's calling and what this is regarding?"
            await self.voice_controller.speak(greeting)
            await asyncio.sleep(2)
            caller_response = await self.voice_controller.listen_for_command(timeout=10)
            if caller_response:
                summary = await self._generate_caller_summary(caller_response.text, contact)
                await self._notify_callbacks("call_screened", {"call": call, "summary": summary})
            return True
        except Exception:
            return False

    async def _generate_caller_summary(self, caller_input: str, contact: ContactProfile) -> str:
        if not self.llm_router:
            return caller_input[:100]
        prompt = f"Summarize this caller's message in 1-2 sentences: {caller_input}"
        try:
            return await self.llm_router.generate(prompt, model_tier="nano")
        except Exception:
            return caller_input[:100]

    async def _start_call_transcription(self, call: CallRecord):
        await self.call_manager.start_recording()
        call.is_recorded = True

    async def handle_sms_with_ai(self, message: SMSMessage) -> Optional[str]:
        contact = self._get_or_create_contact(message.phone_number)
        should_reply = await self._should_auto_reply(message, contact)
        if should_reply:
            reply = await self._generate_smart_reply(message, contact)
            if reply:
                await self.sms_manager.send_message(message.phone_number, reply)
                message.auto_replied = True
                return reply
        return None

    async def _should_auto_reply(self, message: SMSMessage, contact: ContactProfile) -> bool:
        if contact.priority >= 8:
            return True
        if "urgent" in message.body.lower() or "emergency" in message.body.lower():
            return True
        return False

    async def _generate_smart_reply(self, message: SMSMessage, contact: ContactProfile) -> Optional[str]:
        if not self.llm_router:
            return "I'll get back to you soon."
        prompt = f"""Generate a brief, natural reply to this SMS from {contact.name or message.phone_number}:

Their message: {message.body}

Reply (keep it under 100 characters):"""
        try:
            return await self.llm_router.generate(prompt, model_tier="nano")
        except Exception:
            return "I'll get back to you soon."

    def _get_or_create_contact(self, phone_number: str) -> ContactProfile:
        if phone_number not in self._contacts:
            self._contacts[phone_number] = ContactProfile(
                phone_number=phone_number,
                name=None,
                relationship="unknown",
                priority=5,
                last_interaction=None,
                interaction_count=0,
                preferred_contact_method="call",
            )
        return self._contacts[phone_number]

    def add_contact(self, phone_number: str, name: str, relationship: str = "unknown", priority: int = 5):
        self._contacts[phone_number] = ContactProfile(
            phone_number=phone_number,
            name=name,
            relationship=relationship,
            priority=priority,
            last_interaction=datetime.now(),
            interaction_count=0,
            preferred_contact_method="call",
        )

    def update_contact(self, phone_number: str, **kwargs):
        if phone_number in self._contacts:
            contact = self._contacts[phone_number]
            for key, value in kwargs.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)

    def enable_do_not_disturb(self, exceptions: Optional[List[str]] = None):
        self._do_not_disturb = True
        if exceptions:
            self._dnd_exceptions = set(exceptions)

    def disable_do_not_disturb(self):
        self._do_not_disturb = False
        self._dnd_exceptions.clear()

    def set_ai_personality(self, personality: str):
        self._ai_personality = personality

    def get_action_history(self, limit: int = 100) -> List[AIActionResult]:
        return self._action_history[-limit:]

    def register_callback(self, callback: Callable):
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

    async def transcribe_voicemail(self, audio_path: str) -> Optional[str]:
        return await self.voice_controller.transcribe_audio_file(audio_path)

    async def get_phone_summary(self) -> Dict[str, Any]:
        status = await self.phone_manager.get_status()
        current_call = await self.call_manager.get_current_call()
        unread_sms = await self.sms_manager.get_unread_count()
        return {
            "device_connected": status.is_connected,
            "battery_level": status.battery_level,
            "signal_strength": status.signal_strength,
            "active_call": current_call is not None,
            "unread_messages": unread_sms,
            "ai_mode": "active" if self._active else "inactive",
            "do_not_disturb": self._do_not_disturb,
            "contacts_managed": len(self._contacts),
            "actions_today": len([a for a in self._action_history if a.executed_at.date() == datetime.now().date()]),
        }
