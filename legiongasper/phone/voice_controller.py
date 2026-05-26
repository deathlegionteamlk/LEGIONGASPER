import asyncio
import os
import tempfile
import wave
import json
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import subprocess


@dataclass
class VoiceCommand:
    command_id: str
    text: str
    confidence: float
    timestamp: datetime
    action_taken: Optional[str] = None


@dataclass
class WakeWordConfig:
    word: str
    sensitivity: float
    callback: Callable


class VoiceController:
    def __init__(self, phone_manager=None):
        self.phone_manager = phone_manager
        self._wake_words: Dict[str, WakeWordConfig] = {}
        self._command_handlers: Dict[str, Callable] = {}
        self._is_listening = False
        self._listen_task: Optional[asyncio.Task] = None
        self._command_history: List[VoiceCommand] = []
        self._audio_buffer: bytes = b""
        self._lock = asyncio.Lock()
        self._tts_enabled = True
        self._stt_enabled = True

    async def initialize(self):
        try:
            import speech_recognition as sr
            import pyttsx3
            self.sr = sr
            self.tts_engine = pyttsx3.init()
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            return True
        except ImportError:
            return False

    async def text_to_speech(self, text: str, save_path: Optional[str] = None) -> Optional[str]:
        if not self._tts_enabled:
            return None
        try:
            if save_path:
                self.tts_engine.save_to_file(text, save_path)
                self.tts_engine.runAndWait()
                return save_path
            else:
                temp_path = tempfile.mktemp(suffix=".mp3")
                self.tts_engine.save_to_file(text, temp_path)
                self.tts_engine.runAndWait()
                return temp_path
        except Exception:
            return None

    async def speech_to_text(self, audio_path: Optional[str] = None, duration: int = 5) -> Optional[str]:
        if not self._stt_enabled:
            return None
        try:
            if audio_path:
                with self.sr.AudioFile(audio_path) as source:
                    audio = self.recognizer.record(source)
            else:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=duration)
            text = self.recognizer.recognize_google(audio)
            return text
        except Exception:
            return None

    async def start_listening(self):
        if self._is_listening:
            return
        self._is_listening = True
        self._listen_task = asyncio.create_task(self._listen_loop())

    async def stop_listening(self):
        self._is_listening = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

    async def _listen_loop(self):
        while self._is_listening:
            try:
                text = await self.speech_to_text(duration=3)
                if text:
                    await self._process_voice_input(text)
                await asyncio.sleep(0.1)
            except Exception:
                await asyncio.sleep(0.5)

    async def _process_voice_input(self, text: str):
        confidence = 0.9
        for wake_word, config in self._wake_words.items():
            if wake_word.lower() in text.lower():
                try:
                    if asyncio.iscoroutinefunction(config.callback):
                        await config.callback(text)
                    else:
                        config.callback(text)
                except Exception:
                    pass
                return
        command = VoiceCommand(
            command_id=f"cmd_{datetime.now().timestamp()}",
            text=text,
            confidence=confidence,
            timestamp=datetime.now(),
        )
        action = await self._execute_command(text)
        command.action_taken = action
        self._command_history.append(command)

    async def _execute_command(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for command_key, handler in self._command_handlers.items():
            if command_key in text_lower:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(text)
                    else:
                        result = handler(text)
                    return str(result) if result else command_key
                except Exception:
                    return None
        return None

    def register_wake_word(self, word: str, callback: Callable, sensitivity: float = 0.8):
        self._wake_words[word.lower()] = WakeWordConfig(
            word=word.lower(),
            sensitivity=sensitivity,
            callback=callback,
        )

    def unregister_wake_word(self, word: str):
        self._wake_words.pop(word.lower(), None)

    def register_command_handler(self, command: str, handler: Callable):
        self._command_handlers[command.lower()] = handler

    def unregister_command_handler(self, command: str):
        self._command_handlers.pop(command.lower(), None)

    async def record_audio(self, duration: int = 5, sample_rate: int = 16000) -> Optional[str]:
        try:
            temp_path = tempfile.mktemp(suffix=".wav")
            proc = await asyncio.create_subprocess_exec(
                "arecord", "-d", str(duration), "-r", str(sample_rate), "-f", "S16_LE", temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            if proc.returncode == 0:
                return temp_path
            return None
        except Exception:
            return None

    async def play_audio(self, audio_path: str) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                "aplay", audio_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    async def transcribe_audio_file(self, audio_path: str) -> Optional[str]:
        return await self.speech_to_text(audio_path)

    def get_command_history(self, limit: int = 50) -> List[VoiceCommand]:
        return self._command_history[-limit:]

    def enable_tts(self):
        self._tts_enabled = True

    def disable_tts(self):
        self._tts_enabled = False

    def enable_stt(self):
        self._stt_enabled = True

    def disable_stt(self):
        self._stt_enabled = False

    async def speak(self, text: str) -> bool:
        path = await self.text_to_speech(text)
        if path:
            return await self.play_audio(path)
        return False

    async def listen_for_command(self, timeout: int = 10) -> Optional[VoiceCommand]:
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            text = await self.speech_to_text(duration=3)
            if text:
                command = VoiceCommand(
                    command_id=f"cmd_{datetime.now().timestamp()}",
                    text=text,
                    confidence=0.9,
                    timestamp=datetime.now(),
                )
                action = await self._execute_command(text)
                command.action_taken = action
                self._command_history.append(command)
                return command
            await asyncio.sleep(0.1)
        return None

    async def process_audio_buffer(self, audio_data: bytes) -> Optional[str]:
        try:
            temp_path = tempfile.mktemp(suffix=".wav")
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
            result = await self.speech_to_text(temp_path)
            os.remove(temp_path)
            return result
        except Exception:
            return None
