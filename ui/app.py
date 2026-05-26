"""
LEGIONGASPER v2.0 - Main Web Application
OpenClaw-like UI with modern design
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import json
from datetime import datetime

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)
app.config['SECRET_KEY'] = 'legion-gasper-v2-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory state (replace with Redis in production)
agents_state = {}
workflows_state = {}
sandboxes_state = {}
channels_state = {}

@app.route('/')
def index():
    """Main dashboard - OpenClaw-like interface"""
    return render_template('dashboard.html')

@app.route('/agents')
def agents_page():
    """Agent manager page"""
    return render_template('agents.html')

@app.route('/workflows')
def workflows_page():
    """Workflow editor page"""
    return render_template('workflows.html')

@app.route('/canvas')
def canvas_page():
    """Canvas visualization page"""
    return render_template('canvas.html')

@app.route('/channels')
def channels_page():
    """Channel configuration page"""
    return render_template('channels.html')

@app.route('/sandboxes')
def sandboxes_page():
    """Sandbox management page"""
    return render_template('sandboxes.html')

@app.route('/browser')
def browser_page():
    """Browser automation page"""
    return render_template('browser.html')

@app.route('/home')
def home_page():
    """Smart home control page"""
    return render_template('home.html')

# API Routes
@app.route('/api/v1/status')
def api_status():
    """System status endpoint"""
    return jsonify({
        "status": "operational",
        "version": "2.0.0",
        "codename": "OpenClaw Killer",
        "team": "DEATH LEGION (DEMO X HEXA)",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "agents": 25,
            "channels": 13,
            "providers": 35,
            "sandboxes": True,
            "browser": True,
            "smart_home": True,
            "cron": True,
            "canvas": True
        }
    })

@app.route('/api/v1/agents', methods=['GET', 'POST'])
def api_agents():
    """Agent management API"""
    if request.method == 'GET':
        return jsonify({
            "agents": list(agents_state.values()),
            "total_slots": 25,
            "used_slots": len(agents_state)
        })
    else:
        data = request.json
        agent_id = f"agent_{len(agents_state) + 1}"
        agents_state[agent_id] = {
            "id": agent_id,
            "name": data.get('name', 'Unnamed Agent'),
            "status": "idle",
            "created_at": datetime.utcnow().isoformat(),
            "config": data
        }
        return jsonify({"success": True, "agent": agents_state[agent_id]})

@app.route('/api/v1/workflows', methods=['GET', 'POST'])
def api_workflows():
    """Workflow management API"""
    if request.method == 'GET':
        return jsonify({"workflows": list(workflows_state.values())})
    else:
        data = request.json
        workflow_id = f"workflow_{len(workflows_state) + 1}"
        workflows_state[workflow_id] = {
            "id": workflow_id,
            "name": data.get('name', 'Unnamed Workflow'),
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "nodes": data.get('nodes', []),
            "edges": data.get('edges', [])
        }
        return jsonify({"success": True, "workflow": workflows_state[workflow_id]})

@app.route('/api/v1/sandboxes', methods=['GET', 'POST'])
def api_sandboxes():
    """Sandbox management API"""
    if request.method == 'GET':
        return jsonify({
            "sandboxes": list(sandboxes_state.values()),
            "providers": ["e2b", "daytona", "local"]
        })
    else:
        data = request.json
        sandbox_id = f"sandbox_{len(sandboxes_state) + 1}"
        sandboxes_state[sandbox_id] = {
            "id": sandbox_id,
            "provider": data.get('provider', 'local'),
            "status": "creating",
            "created_at": datetime.utcnow().isoformat(),
            "config": data
        }
        return jsonify({"success": True, "sandbox": sandboxes_state[sandbox_id]})

@app.route('/api/v1/channels', methods=['GET'])
def api_channels():
    """Channel configuration API"""
    return jsonify({
        "channels": [
            {"id": "discord", "name": "Discord", "enabled": True},
            {"id": "slack", "name": "Slack", "enabled": True},
            {"id": "telegram", "name": "Telegram", "enabled": True},
            {"id": "whatsapp", "name": "WhatsApp", "enabled": True},
            {"id": "email", "name": "Email", "enabled": True},
            {"id": "sms", "name": "SMS", "enabled": True},
            {"id": "matrix", "name": "Matrix", "enabled": True},
            {"id": "signal", "name": "Signal", "enabled": True},
            {"id": "messenger", "name": "Messenger", "enabled": True},
            {"id": "teams", "name": "Microsoft Teams", "enabled": True},
            {"id": "webhook", "name": "Webhook", "enabled": True},
            {"id": "websocket", "name": "WebSocket", "enabled": True},
            {"id": "pgone", "name": "PGOne/HJIM", "enabled": True}
        ]
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to LEGIONGASPER v2.0'})

@socketio.on('agent_command')
def handle_agent_command(data):
    emit('agent_response', {'agent': data.get('agent_id'), 'result': 'Command executed'})

@socketio.on('workflow_execute')
def handle_workflow_execute(data):
    emit('workflow_status', {'workflow': data.get('workflow_id'), 'status': 'running'})

def run_app(host='0.0.0.0', port=8080, debug=False):
    """Run the Flask-SocketIO application"""
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_app()
