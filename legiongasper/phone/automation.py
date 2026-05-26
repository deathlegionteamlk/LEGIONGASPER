import asyncio
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from .manager import PhoneManager
from .call_manager import CallManager, CallRecord
from .sms_manager import SMSManager, SMSMessage
from .voice_controller import VoiceController
from .pgone_manager import PGOneManager


@dataclass
class ScheduledAction:
    action_id: str
    action_type: str
    scheduled_time: datetime
    params: Dict[str, Any]
    executed: bool = False
    result: Optional[str] = None


@dataclass
class SmartReply:
    original_message: str
    suggestions: List[str]
    generated_at: datetime
    confidence_scores: List[float]


@dataclass
class VoicemailTranscription:
    audio_path: str
    transcription: str
    summary: str
    caller_number: Optional[str]
    duration: int
    transcribed_at: datetime


class PhoneAutomation:
    def __init__(self, phone_manager: PhoneManager, pgone_manager: PGOneManager, llm_router=None):
        self.phone_manager = phone_manager
        self.pgone_manager = pgone_manager
        self.call_manager = pgone_manager.call_manager
        self.sms_manager = pgone_manager.sms_manager
        self.voice_controller = pgone_manager.voice_controller
        self.llm_router = llm_router
        self._scheduled_actions: List[ScheduledAction] = []
        self._scheduler_task: Optional[asyncio.Task] = None
        self._active = False
        self._auto_answer_ai = False
        self._ai_greeting = "Hello, this is an AI assistant. How may I help you?"
        self._voicemail_transcriptions: List[VoicemailTranscription] = []
        self._smart_replies: List[SmartReply] = []
        self._spam_detection_enabled = True
        self._spam_score_threshold = 0.7
        self._callbacks: List[Callable] = []

    async def start(self):
        self._active = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.call_manager.register_state_callback(self._on_call_state_change)
        self.sms_manager.register_message_callback(self._on_new_message)

    async def stop(self):
        self._active = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

    async def _scheduler_loop(self):
        while self._active:
            try:
                now = datetime.now()
                for action in self._scheduled_actions:
                    if not action.executed and action.scheduled_time <= now:
                        await self._execute_scheduled_action(action)
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(5)

    async def _execute_scheduled_action(self, action: ScheduledAction):
        try:
            if action.action_type == "send_sms":
                result = await self.sms_manager.send_message(
                    action.params["phone_number"],
                    action.params["message"]
                )
                action.result = "sent" if result else "failed"
            elif action.action_type == "call":
                result = await self.call_manager.dial_number(action.params["phone_number"])
                action.result = "dialed" if result else "failed"
            elif action.action_type == "reminder":
                await self._notify_callbacks("reminder", action.params)
                action.result = "notified"
            action.executed = True
        except Exception as e:
            action.result = f"error: {str(e)}"
            action.executed = True

    async def _on_call_state_change(self, old_state, new_state, status):
        if new_state.value == "ringing" and self._auto_answer_ai:
            await asyncio.sleep(2)
            await self.call_manager.answer_call()
            await asyncio.sleep(0.5)
            await self.voice_controller.speak(self._ai_greeting)

    async def _on_new_message(self, message: SMSMessage):
        if self._spam_detection_enabled:
            spam_score = self._calculate_spam_score(message.body)
            if spam_score > self._spam_score_threshold:
                return
        await self.pgone_manager.handle_sms_with_ai(message)

    def _calculate_spam_score(self, text: str) -> float:
        spam_keywords = ["win", "prize", "free", "offer", "limited", "click", "urgent", "act now", "congratulations"]
        text_lower = text.lower()
        score = sum(1 for kw in spam_keywords if kw in text_lower) / len(spam_keywords)
        return min(1.0, score * 2)

    async def schedule_sms(self, phone_number: str, message: str, send_at: datetime) -> str:
        action = ScheduledAction(
            action_id=f"sched_{datetime.now().timestamp()}",
            action_type="send_sms",
            scheduled_time=send_at,
            params={"phone_number": phone_number, "message": message},
        )
        self._scheduled_actions.append(action)
        return action.action_id

    async def schedule_call(self, phone_number: str, call_at: datetime) -> str:
        action = ScheduledAction(
            action_id=f"sched_{datetime.now().timestamp()}",
            action_type="call",
            scheduled_time=call_at,
            params={"phone_number": phone_number},
        )
        self._scheduled_actions.append(action)
        return action.action_id

    async def get_smart_reply_suggestions(self, message_text: str, context: Optional[str] = None) -> SmartReply:
        if not self.llm_router:
            return SmartReply(
                original_message=message_text,
                suggestions=["I'll get back to you.", "Thanks for the message.", "Can we talk later?"],
                generated_at=datetime.now(),
                confidence_scores=[0.5, 0.5, 0.5],
            )
        prompt = f"""Generate 3 contextual reply suggestions for this message:

Message: {message_text}
{f"Context: {context}" if context else ""}

Provide JSON: {{"suggestions": ["reply1", "reply2", "reply3"], "confidence": [0.9, 0.8, 0.7]}}"""
        try:
            response = await self.llm_router.generate(prompt, model_tier="nano")
            data = json.loads(response.strip())
            suggestions = data.get("suggestions", ["Reply 1", "Reply 2", "Reply 3"])[:3]
            confidence = data.get("confidence", [0.8, 0.7, 0.6])[:3]
            smart_reply = SmartReply(
                original_message=message_text,
                suggestions=suggestions,
                generated_at=datetime.now(),
                confidence_scores=confidence,
            )
            self._smart_replies.append(smart_reply)
            return smart_reply
        except Exception:
            return SmartReply(
                original_message=message_text,
                suggestions=["I'll get back to you.", "Thanks for the message.", "Can we talk later?"],
                generated_at=datetime.now(),
                confidence_scores=[0.5, 0.5, 0.5],
            )

    async def transcribe_voicemail(self, audio_path: str, caller_number: Optional[str] = None) -> VoicemailTranscription:
        transcription = await self.voice_controller.transcribe_audio_file(audio_path)
        summary = ""
        if self.llm_router and transcription:
            prompt = f"Summarize this voicemail in one sentence: {transcription}"
            summary = await self.llm_router.generate(prompt, model_tier="nano")
        vt = VoicemailTranscription(
            audio_path=audio_path,
            transcription=transcription or "",
            summary=summary,
            caller_number=caller_number,
            duration=0,
            transcribed_at=datetime.now(),
        )
        self._voicemail_transcriptions.append(vt)
        return vt

    def enable_auto_answer_with_ai(self, greeting: Optional[str] = None):
        self._auto_answer_ai = True
        if greeting:
            self._ai_greeting = greeting

    def disable_auto_answer_with_ai(self):
        self._auto_answer_ai = False

    def set_ai_greeting(self, greeting: str):
        self._ai_greeting = greeting

    def enable_spam_detection(self, threshold: float = 0.7):
        self._spam_detection_enabled = True
        self._spam_score_threshold = threshold

    def disable_spam_detection(self):
        self._spam_detection_enabled = False

    def get_scheduled_actions(self) -> List[ScheduledAction]:
        return [a for a in self._scheduled_actions if not a.executed]

    def get_voicemail_transcriptions(self, limit: int = 50) -> List[VoicemailTranscription]:
        return self._voicemail_transcriptions[-limit:]

    def get_smart_reply_history(self, limit: int = 50) -> List[SmartReply]:
        return self._smart_replies[-limit:]

    def cancel_scheduled_action(self, action_id: str) -> bool:
        for action in self._scheduled_actions:
            if action.action_id == action_id and not action.executed:
                action.executed = True
                action.result = "cancelled"
                return True
        return False

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

    async def screen_call_with_questions(self, questions: List[str]) -> Dict[str, Any]:
        await self.voice_controller.speak("Hello, I'm screening this call. May I ask a few questions?")
        answers = []
        for question in questions:
            await self.voice_controller.speak(question)
            await asyncio.sleep(1)
            response = await self.voice_controller.listen_for_command(timeout=10)
            answers.append({
                "question": question,
                "answer": response.text if response else "No response",
            })
        return {
            "screened_at": datetime.now(),
            "questions": questions,
            "answers": answers,
        }

    async def get_automation_status(self) -> Dict[str, Any]:
        return {
            "active": self._active,
            "auto_answer_ai": self._auto_answer_ai,
            "spam_detection": self._spam_detection_enabled,
            "scheduled_pending": len(self.get_scheduled_actions()),
            "voicemails_transcribed": len(self._voicemail_transcriptions),
            "smart_replies_generated": len(self._smart_replies),
        }
