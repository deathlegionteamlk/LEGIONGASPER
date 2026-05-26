import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ..phone.manager import PhoneManager
from ..phone.call_manager import CallManager
from ..phone.sms_manager import SMSManager
from ..phone.voice_controller import VoiceController
from ..phone.pgone_manager import PGOneManager
from ..phone.automation import PhoneAutomation


class PhoneDashboard:
    def __init__(self, phone_manager: PhoneManager, pgone_manager: PGOneManager):
        self.phone_manager = phone_manager
        self.pgone_manager = pgone_manager
        self.call_manager = pgone_manager.call_manager
        self.sms_manager = pgone_manager.sms_manager
        self.voice_controller = pgone_manager.voice_controller
        self.automation = None
        self.active_connections: List[WebSocket] = []
        self.router = APIRouter()
        self._setup_routes()
        self._monitor_task: Optional[asyncio.Task] = None

    def _setup_routes(self):
        self.router.add_api_route("/phone", self.get_dashboard, response_class=HTMLResponse)
        self.router.add_api_route("/phone/api/status", self.get_status)
        self.router.add_api_route("/phone/api/calls", self.get_calls)
        self.router.add_api_route("/phone/api/sms", self.get_sms)
        self.router.add_api_route("/phone/api/contacts", self.get_contacts)
        self.router.add_api_route("/phone/api/pgone/actions", self.get_pgone_actions)
        self.router.add_websocket_route("/phone/ws", self.websocket_endpoint)

    async def start_monitoring(self):
        self._monitor_task = asyncio.create_task(self._broadcast_loop())

    async def stop_monitoring(self):
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _broadcast_loop(self):
        while True:
            try:
                status = await self._get_full_status()
                await self._broadcast(json.dumps({"type": "status", "data": status}))
                await asyncio.sleep(2)
            except Exception:
                await asyncio.sleep(5)

    async def _broadcast(self, message: str):
        disconnected = []
        for conn in self.active_connections:
            try:
                await conn.send_text(message)
            except Exception:
                disconnected.append(conn)
        for conn in disconnected:
            self.active_connections.remove(conn)

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    await self._handle_websocket_message(websocket, msg)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)

    async def _handle_websocket_message(self, websocket: WebSocket, msg: Dict[str, Any]):
        action = msg.get("action")
        if action == "dial":
            number = msg.get("number", "")
            if number:
                result = await self.call_manager.dial_number(number)
                await websocket.send_text(json.dumps({"type": "action_result", "action": "dial", "success": result}))
        elif action == "answer":
            result = await self.call_manager.answer_call()
            await websocket.send_text(json.dumps({"type": "action_result", "action": "answer", "success": result}))
        elif action == "reject":
            result = await self.call_manager.reject_call()
            await websocket.send_text(json.dumps({"type": "action_result", "action": "reject", "success": result}))
        elif action == "send_sms":
            number = msg.get("number", "")
            text = msg.get("text", "")
            if number and text:
                result = await self.sms_manager.send_message(number, text)
                await websocket.send_text(json.dumps({"type": "action_result", "action": "send_sms", "success": result}))
        elif action == "toggle_dnd":
            self.pgone_manager._do_not_disturb = not self.pgone_manager._do_not_disturb
            await websocket.send_text(json.dumps({"type": "dnd_status", "enabled": self.pgone_manager._do_not_disturb}))

    async def get_dashboard(self) -> HTMLResponse:
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LEGIONGASPER Phone Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .slide-in { animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    </style>
</head>
<body class="bg-slate-900 text-white min-h-screen">
    <div class="container mx-auto p-4 max-w-7xl">
        <header class="mb-6">
            <h1 class="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                <i class="fas fa-mobile-alt mr-3"></i>LEGIONGASPER Phone
            </h1>
            <p class="text-slate-400 mt-1">HJIM AI Controller - Autonomous Phone Management</p>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div class="glass rounded-xl p-4 border border-slate-700">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-slate-400 text-sm">Device Status</p>
                        <p id="device-status" class="text-xl font-semibold text-emerald-400">Disconnected</p>
                    </div>
                    <i class="fas fa-mobile-alt text-3xl text-slate-600"></i>
                </div>
                <div class="mt-3">
                    <div class="flex justify-between text-sm">
                        <span class="text-slate-400">Battery</span>
                        <span id="battery-level" class="text-cyan-400">--%</span>
                    </div>
                    <div class="w-full bg-slate-700 rounded-full h-2 mt-1">
                        <div id="battery-bar" class="bg-cyan-500 h-2 rounded-full" style="width: 0%"></div>
                    </div>
                </div>
            </div>

            <div class="glass rounded-xl p-4 border border-slate-700">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-slate-400 text-sm">Active Call</p>
                        <p id="call-status" class="text-xl font-semibold text-slate-300">None</p>
                    </div>
                    <i class="fas fa-phone text-3xl text-slate-600"></i>
                </div>
                <div class="mt-3 flex gap-2">
                    <button onclick="answerCall()" class="flex-1 bg-emerald-600 hover:bg-emerald-500 py-2 rounded-lg text-sm transition">
                        <i class="fas fa-phone mr-1"></i> Answer
                    </button>
                    <button onclick="rejectCall()" class="flex-1 bg-rose-600 hover:bg-rose-500 py-2 rounded-lg text-sm transition">
                        <i class="fas fa-phone-slash mr-1"></i> Reject
                    </button>
                </div>
            </div>

            <div class="glass rounded-xl p-4 border border-slate-700">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-slate-400 text-sm">Unread SMS</p>
                        <p id="unread-count" class="text-2xl font-semibold text-amber-400">0</p>
                    </div>
                    <i class="fas fa-envelope text-3xl text-slate-600"></i>
                </div>
                <div class="mt-3">
                    <button onclick="showSMSPanel()" class="w-full bg-slate-700 hover:bg-slate-600 py-2 rounded-lg text-sm transition">
                        <i class="fas fa-inbox mr-1"></i> View Inbox
                    </button>
                </div>
            </div>

            <div class="glass rounded-xl p-4 border border-slate-700">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-slate-400 text-sm">AI Mode</p>
                        <p id="ai-status" class="text-xl font-semibold text-violet-400">Active</p>
                    </div>
                    <i class="fas fa-robot text-3xl text-slate-600"></i>
                </div>
                <div class="mt-3 flex gap-2">
                    <button onclick="toggleDND()" id="dnd-btn" class="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg text-sm transition">
                        <i class="fas fa-moon mr-1"></i> DND
                    </button>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div class="lg:col-span-2 glass rounded-xl p-4 border border-slate-700">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-lg font-semibold"><i class="fas fa-phone-alt mr-2 text-cyan-400"></i>Call Controls</h2>
                    <span id="signal-strength" class="text-sm text-slate-400"><i class="fas fa-signal mr-1"></i>--</span>
                </div>
                <div class="flex gap-2 mb-4">
                    <input type="tel" id="dial-number" placeholder="Enter phone number" 
                           class="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500">
                    <button onclick="dialNumber()" class="bg-cyan-600 hover:bg-cyan-500 px-6 py-2 rounded-lg transition">
                        <i class="fas fa-phone"></i> Dial
                    </button>
                </div>
                <div id="call-log" class="space-y-2 max-h-64 overflow-y-auto">
                    <p class="text-slate-500 text-center py-4">No recent calls</p>
                </div>
            </div>

            <div class="glass rounded-xl p-4 border border-slate-700">
                <h2 class="text-lg font-semibold mb-4"><i class="fas fa-comment-alt mr-2 text-violet-400"></i>Quick SMS</h2>
                <div class="space-y-3">
                    <input type="tel" id="sms-number" placeholder="Phone number" 
                           class="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500">
                    <textarea id="sms-text" placeholder="Message..." rows="3"
                              class="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500 resize-none"></textarea>
                    <button onclick="sendSMS()" class="w-full bg-violet-600 hover:bg-violet-500 py-2 rounded-lg text-sm transition">
                        <i class="fas fa-paper-plane mr-1"></i> Send
                    </button>
                </div>
            </div>
        </div>

        <div class="mt-4 glass rounded-xl p-4 border border-slate-700">
            <h2 class="text-lg font-semibold mb-4"><i class="fas fa-brain mr-2 text-pink-400"></i>PGOne (HJIM) Activity Log</h2>
            <div id="pgone-log" class="space-y-2 max-h-48 overflow-y-auto text-sm">
                <p class="text-slate-500 text-center py-4">No AI actions yet</p>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket(`wss://${window.location.host}/phone/ws`);
        
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'status') updateStatus(msg.data);
            if (msg.type === 'action_result') showNotification(msg.action, msg.success);
        };

        function updateStatus(data) {
            document.getElementById('device-status').textContent = data.device_connected ? 'Connected' : 'Disconnected';
            document.getElementById('device-status').className = data.device_connected ? 'text-xl font-semibold text-emerald-400' : 'text-xl font-semibold text-rose-400';
            document.getElementById('battery-level').textContent = data.battery_level + '%';
            document.getElementById('battery-bar').style.width = data.battery_level + '%';
            document.getElementById('call-status').textContent = data.active_call ? 'In Call' : 'None';
            document.getElementById('unread-count').textContent = data.unread_messages;
            document.getElementById('signal-strength').innerHTML = `<i class="fas fa-signal mr-1"></i>${data.signal_strength || '--'}`;
            document.getElementById('ai-status').textContent = data.ai_mode === 'active' ? 'Active' : 'Inactive';
            
            if (data.recent_calls) {
                const callLog = document.getElementById('call-log');
                callLog.innerHTML = data.recent_calls.map(c => `
                    <div class="flex items-center justify-between bg-slate-800 p-2 rounded slide-in">
                        <div>
                            <p class="font-medium">${c.number}</p>
                            <p class="text-xs text-slate-400">${c.type} - ${c.time}</p>
                        </div>
                        <span class="text-xs ${c.duration > 0 ? 'text-emerald-400' : 'text-slate-500'}">${c.duration}s</span>
                    </div>
                `).join('');
            }
            
            if (data.pgone_actions) {
                const pgoneLog = document.getElementById('pgone-log');
                pgoneLog.innerHTML = data.pgone_actions.map(a => `
                    <div class="flex items-center gap-3 bg-slate-800 p-2 rounded slide-in">
                        <i class="fas fa-robot text-pink-400"></i>
                        <div class="flex-1">
                            <p class="font-medium">${a.action}</p>
                            <p class="text-xs text-slate-400">${a.reasoning}</p>
                        </div>
                        <span class="text-xs text-cyan-400">${a.confidence}%</span>
                    </div>
                `).join('');
            }
        }

        function dialNumber() {
            const num = document.getElementById('dial-number').value;
            if (num) ws.send(JSON.stringify({action: 'dial', number: num}));
        }

        function answerCall() {
            ws.send(JSON.stringify({action: 'answer'}));
        }

        function rejectCall() {
            ws.send(JSON.stringify({action: 'reject'}));
        }

        function sendSMS() {
            const num = document.getElementById('sms-number').value;
            const text = document.getElementById('sms-text').value;
            if (num && text) {
                ws.send(JSON.stringify({action: 'send_sms', number: num, text: text}));
                document.getElementById('sms-text').value = '';
            }
        }

        function toggleDND() {
            ws.send(JSON.stringify({action: 'toggle_dnd'}));
        }

        function showNotification(action, success) {
            const div = document.createElement('div');
            div.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg ${success ? 'bg-emerald-600' : 'bg-rose-600'} slide-in`;
            div.textContent = action + (success ? ' succeeded' : ' failed');
            document.body.appendChild(div);
            setTimeout(() => div.remove(), 3000);
        }

        function showSMSPanel() {
            alert('SMS Inbox - Feature coming soon');
        }
    </script>
</body>
</html>"""
        return HTMLResponse(content=html)

    async def get_status(self) -> Dict[str, Any]:
        status = await self.phone_manager.get_status()
        summary = await self.pgone_manager.get_phone_summary()
        return {
            "device_connected": status.is_connected,
            "battery_level": status.battery_level,
            "signal_strength": status.signal_strength,
            "network_type": status.network_type,
            "active_call": summary.get("active_call", False),
            "unread_messages": summary.get("unread_messages", 0),
            "ai_mode": summary.get("ai_mode", "inactive"),
            "do_not_disturb": summary.get("do_not_disturb", False),
        }

    async def get_calls(self) -> Dict[str, Any]:
        history = await self.call_manager.get_call_history(limit=20)
        current = await self.call_manager.get_current_call()
        return {
            "current_call": {
                "number": current.phone_number if current else None,
                "state": current.state.value if current else None,
            },
            "history": [
                {
                    "number": c.phone_number,
                    "type": c.call_type.value,
                    "duration": c.duration,
                    "time": c.end_time.isoformat() if c.end_time else None,
                }
                for c in history
            ],
        }

    async def get_sms(self) -> Dict[str, Any]:
        threads = await self.sms_manager.get_threads(limit=20)
        return {
            "threads": [
                {
                    "id": t.thread_id,
                    "number": t.phone_number,
                    "name": t.contact_name,
                    "last_message": t.last_message[:50] + "..." if len(t.last_message) > 50 else t.last_message,
                    "unread": t.unread_count,
                    "timestamp": t.last_timestamp.isoformat(),
                }
                for t in threads
            ],
        }

    async def get_contacts(self) -> Dict[str, Any]:
        return {
            "contacts": [
                {
                    "number": c.phone_number,
                    "name": c.name,
                    "relationship": c.relationship,
                    "priority": c.priority,
                }
                for c in self.pgone_manager._contacts.values()
            ],
        }

    async def get_pgone_actions(self) -> Dict[str, Any]:
        actions = self.pgone_manager.get_action_history(limit=20)
        return {
            "actions": [
                {
                    "action": a.action.value,
                    "confidence": round(a.confidence * 100, 1),
                    "reasoning": a.reasoning,
                    "success": a.success,
                    "timestamp": a.executed_at.isoformat(),
                }
                for a in actions
            ],
        }

    async def _get_full_status(self) -> Dict[str, Any]:
        status = await self.get_status()
        calls = await self.get_calls()
        pgone = await self.get_pgone_actions()
        return {
            **status,
            "recent_calls": calls.get("history", []),
            "pgone_actions": pgone.get("actions", []),
        }
