import asyncio
import re
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    INBOX = "inbox"
    SENT = "sent"
    DRAFT = "draft"
    OUTBOX = "outbox"


@dataclass
class SMSMessage:
    message_id: str
    phone_number: str
    contact_name: Optional[str]
    body: str
    message_type: MessageType
    timestamp: datetime
    is_read: bool
    thread_id: str
    ai_reply_suggestion: Optional[str] = None
    auto_replied: bool = False


@dataclass
class SMSThread:
    thread_id: str
    phone_number: str
    contact_name: Optional[str]
    last_message: str
    last_timestamp: datetime
    message_count: int
    unread_count: int


class SMSManager:
    def __init__(self, phone_manager, llm_router=None):
        self.phone_manager = phone_manager
        self.llm_router = llm_router
        self._message_callbacks: List[Callable] = []
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._auto_reply_enabled = False
        self._auto_reply_contacts: set = set()
        self._spam_keywords: set = {"spam", "promo", "offer", "win", "prize", "free", "click here", "limited time"}
        self._last_message_count = 0

    async def start_monitoring(self):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_messages())

    async def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitor_messages(self):
        while self._monitoring:
            try:
                inbox = await self.get_messages(MessageType.INBOX, limit=1)
                current_count = len(inbox)
                if current_count > self._last_message_count:
                    new_messages = await self.get_messages(MessageType.INBOX, limit=current_count - self._last_message_count)
                    for msg in new_messages:
                        await self._handle_new_message(msg)
                    self._last_message_count = current_count
                await asyncio.sleep(2)
            except Exception:
                await asyncio.sleep(5)

    async def _handle_new_message(self, message: SMSMessage):
        if self._is_spam(message.body):
            return
        if self._auto_reply_enabled:
            if not self._auto_reply_contacts or message.phone_number in self._auto_reply_contacts:
                reply = await self._generate_ai_reply(message)
                if reply:
                    await self.send_message(message.phone_number, reply)
                    message.auto_replied = True
        for callback in self._message_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception:
                pass

    def _is_spam(self, body: str) -> bool:
        body_lower = body.lower()
        return any(keyword in body_lower for keyword in self._spam_keywords)

    async def _generate_ai_reply(self, message: SMSMessage) -> Optional[str]:
        if not self.llm_router:
            return None
        try:
            prompt = f"Generate a brief, contextual reply to this SMS:\n\nFrom: {message.contact_name or message.phone_number}\nMessage: {message.body}\n\nReply:"
            response = await self.llm_router.generate(prompt, model_tier="nano")
            return response.strip() if response else None
        except Exception:
            return None

    async def get_messages(self, message_type: MessageType = MessageType.INBOX, limit: int = 100) -> List[SMSMessage]:
        try:
            uri_map = {
                MessageType.INBOX: "content://sms/inbox",
                MessageType.SENT: "content://sms/sent",
                MessageType.DRAFT: "content://sms/draft",
            }
            uri = uri_map.get(message_type, "content://sms/inbox")
            result = await self.phone_manager.execute_shell_command(f"content query --uri {uri} --projection _id:address:person:body:date:read:thread_id --limit {limit}")
            messages = []
            for line in result.split("\n"):
                if "_id=" in line:
                    msg = self._parse_message_line(line, message_type)
                    if msg:
                        messages.append(msg)
            return messages
        except Exception:
            return []

    def _parse_message_line(self, line: str, message_type: MessageType) -> Optional[SMSMessage]:
        try:
            parts = line.split(", ")
            data = {}
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    data[key.strip()] = value.strip()
            timestamp_ms = int(data.get("date", 0))
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
            return SMSMessage(
                message_id=data.get("_id", "unknown"),
                phone_number=data.get("address", "unknown"),
                contact_name=data.get("person"),
                body=data.get("body", ""),
                message_type=message_type,
                timestamp=timestamp,
                is_read=data.get("read") == "1",
                thread_id=data.get("thread_id", "0"),
            )
        except Exception:
            return None

    async def get_threads(self, limit: int = 50) -> List[SMSThread]:
        try:
            result = await self.phone_manager.execute_shell_command(f"content query --uri content://sms/conversations --projection thread_id:address:person:body:date:message_count:read --limit {limit}")
            threads = []
            for line in result.split("\n"):
                if "thread_id=" in line:
                    thread = self._parse_thread_line(line)
                    if thread:
                        threads.append(thread)
            return threads
        except Exception:
            return []

    def _parse_thread_line(self, line: str) -> Optional[SMSThread]:
        try:
            parts = line.split(", ")
            data = {}
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    data[key.strip()] = value.strip()
            timestamp_ms = int(data.get("date", 0))
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
            return SMSThread(
                thread_id=data.get("thread_id", "0"),
                phone_number=data.get("address", "unknown"),
                contact_name=data.get("person"),
                last_message=data.get("body", ""),
                last_timestamp=timestamp,
                message_count=int(data.get("message_count", 0)),
                unread_count=0 if data.get("read") == "1" else 1,
            )
        except Exception:
            return None

    async def send_message(self, phone_number: str, message: str) -> bool:
        try:
            escaped_message = message.replace("'", "'\"'\"'")
            await self.phone_manager.execute_shell_command(f"am start -a android.intent.action.SENDTO -d sms:{phone_number} --es sms_body '{escaped_message}' --ez exit_on_sent true")
            await asyncio.sleep(0.5)
            await self.phone_manager.execute_shell_command("input keyevent 22")
            await asyncio.sleep(0.2)
            await self.phone_manager.execute_shell_command("input keyevent 66")
            return True
        except Exception:
            return False

    async def delete_message(self, message_id: str) -> bool:
        try:
            await self.phone_manager.execute_shell_command(f"content delete --uri content://sms/{message_id}")
            return True
        except Exception:
            return False

    async def mark_as_read(self, message_id: str) -> bool:
        try:
            await self.phone_manager.execute_shell_command(f"content update --uri content://sms/{message_id} --bind read:i:1")
            return True
        except Exception:
            return False

    async def get_smart_reply_suggestions(self, thread_id: str) -> List[str]:
        try:
            messages = await self.get_thread_messages(thread_id, limit=5)
            if not messages or not self.llm_router:
                return []
            conversation = "\n".join([f"{m.contact_name or m.phone_number}: {m.body}" for m in reversed(messages)])
            prompt = f"Generate 3 brief reply suggestions for this conversation:\n\n{conversation}\n\nSuggestions (one per line):"
            response = await self.llm_router.generate(prompt, model_tier="nano")
            suggestions = [s.strip("- ") for s in response.strip().split("\n") if s.strip()][:3]
            return suggestions
        except Exception:
            return []

    async def get_thread_messages(self, thread_id: str, limit: int = 50) -> List[SMSMessage]:
        try:
            result = await self.phone_manager.execute_shell_command(f"content query --uri content://sms/ --projection _id:address:person:body:date:read:thread_id:type --where \"thread_id={thread_id}\" --limit {limit}")
            messages = []
            for line in result.split("\n"):
                if "_id=" in line:
                    msg = self._parse_message_line(line, MessageType.INBOX)
                    if msg:
                        messages.append(msg)
            return messages
        except Exception:
            return []

    def register_message_callback(self, callback: Callable):
        self._message_callbacks.append(callback)

    def unregister_message_callback(self, callback: Callable):
        if callback in self._message_callbacks:
            self._message_callbacks.remove(callback)

    def enable_auto_reply(self, contacts: Optional[List[str]] = None):
        self._auto_reply_enabled = True
        if contacts:
            self._auto_reply_contacts = set(contacts)

    def disable_auto_reply(self):
        self._auto_reply_enabled = False
        self._auto_reply_contacts.clear()

    def add_spam_keyword(self, keyword: str):
        self._spam_keywords.add(keyword.lower())

    def remove_spam_keyword(self, keyword: str):
        self._spam_keywords.discard(keyword.lower())

    async def search_messages(self, query: str, limit: int = 50) -> List[SMSMessage]:
        all_messages = await self.get_messages(MessageType.INBOX, limit=limit * 2)
        query_lower = query.lower()
        return [m for m in all_messages if query_lower in m.body.lower() or query_lower in m.phone_number][:limit]

    async def get_unread_count(self) -> int:
        try:
            result = await self.phone_manager.execute_shell_command("content query --uri content://sms/inbox --projection read --where \"read=0\"")
            return len([l for l in result.split("\n") if "read=" in l])
        except Exception:
            return 0
