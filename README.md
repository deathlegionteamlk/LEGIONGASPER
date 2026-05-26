# ⚡ LEGIONGASPER

**OpenClaw Factory Edition** - A Python-based Multi-Agent System with Parallel Execution

> *Coded by DEATH LEGION Team (DEMO X HEXA)*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

## 🎯 Overview

LEGIONGASPER is a next-generation autonomous agent framework that surpasses traditional multi-agent systems with **true parallelism**, **captain-agent orchestration**, and **factory-pattern agent management**. Built for scale, designed for intelligence.

### Key Features

- 🚀 **True Parallel Execution** - Asyncio-based concurrent agent execution with semaphore control
- 🧠 **5-Layer Memory Architecture** - Session, Working, Daily, Long-term (Vector DB), and Collective Consciousness
- 👑 **Captain-Agent Pattern** - Intelligent task decomposition with squad formation
- 🏭 **Factory Pattern** - Dynamic agent spawning with pooling and lifecycle management
- 🔀 **Multi-Provider LLM Router** - OpenAI, Anthropic, OpenRouter with tier-based selection
- 🛡️ **Governance Layer** - Audit logging, cost tracking, rate limiting, RBAC
- 📊 **Real-time Dashboard** - WebSocket-powered monitoring and analytics
- 🔌 **REST API & WebSocket Gateway** - Multi-channel communication support

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LEGIONGASPER SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│  Gateway Layer (REST API + WebSocket)                      │
│  └── Port 8081 - External Interface                         │
├─────────────────────────────────────────────────────────────┤
│  Dashboard Layer (FastAPI + WebSocket Real-time)           │
│  └── Port 8080 - Monitoring & Analytics                   │
├─────────────────────────────────────────────────────────────┤
│  Orchestration Layer                                        │
│  ├── Captain (Task Decomposition)                          │
│  ├── Squad (Parallel Execution)                            │
│  └── Orchestrator (Queue + Dependency Resolution)          │
├─────────────────────────────────────────────────────────────┤
│  Agent Layer                                                │
│  ├── Agent Factory (Dynamic Spawning + Pooling)            │
│  ├── Base Agent (Async Execution + State Management)       │
│  └── Tool Registry (Schema + Permission System)            │
├─────────────────────────────────────────────────────────────┤
│  Memory Layer (5-Tier Architecture)                         │
│  ├── Session Memory (TTL Context Buffer)                   │
│  ├── Working Memory (Priority Queue)                       │
│  ├── Daily Memory (Date-indexed Persistence)               │
│  ├── Long-term Memory (ChromaDB Vector Store)              │
│  └── Collective Consciousness (Inter-agent Sharing)        │
├─────────────────────────────────────────────────────────────┤
│  LLM Layer                                                  │
│  └── Multi-Provider Router (OpenAI/Anthropic/OpenRouter)   │
├─────────────────────────────────────────────────────────────┤
│  Governance Layer                                           │
│  ├── Audit Logging                                         │
│  ├── Cost Tracking                                         │
│  ├── Rate Limiting                                         │
│  └── RBAC (Role-Based Access Control)                      │
└─────────────────────────────────────────────────────────────┘
```

### Memory Architecture

The 5-layer memory system provides comprehensive context management:

1. **Session Memory** - Short-term context with TTL, conversation history tracking
2. **Working Memory** - Priority queue for task-focused context with relevance scoring
3. **Daily Memory** - Date-based indexing with persistence and daily summarization
4. **Long-term Memory** - ChromaDB vector embeddings with semantic search
5. **Collective Consciousness** - Inter-agent knowledge sharing with broadcast/subscribe

### Captain-Agent Pattern

```python
# Captain decomposes tasks and forms squads
captain = Captain(agent_id="research_lead")
subtasks = captain.decompose_task("Analyze market trends")
squad = captain.form_squad(subtasks)
results = await squad.execute_parallel()
final = captain.aggregate_results(results)
```

## 🚀 Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/deathlegion/legiongasper.git
cd legiongasper

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python -m legiongasper.cli init
```

### Configuration

Create a `.env` file:

```bash
# LLM Provider API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional: Redis for distributed memory
REDIS_URL=redis://localhost:6379

# Optional: ChromaDB for vector storage
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
```

### Start the Server

```bash
# Start the gateway server (port 8081)
python -m legiongasper.cli serve

# Or with custom ports
python -m legiongasper.cli serve --port 8081 --dashboard-port 8080
```

### Using the CLI

```bash
# Initialize configuration
legiongasper init

# Spawn an agent
legiongasper agent spawn --template research --id researcher_1

# List agents
legiongasper agent list

# Submit a task
legiongasper task submit "Research quantum computing advances" --priority high

# Check system status
legiongasper status
```

### Using the API

```python
import requests

# Spawn an agent
response = requests.post("http://localhost:8081/api/v1/agents/spawn", json={
    "template_id": "research",
    "agent_id": "my_researcher"
})

# Submit a task
response = requests.post("http://localhost:8081/api/v1/tasks/submit", json={
    "description": "Analyze Python async patterns",
    "priority": "high"
})
```

## 📁 Project Structure

```
legiongasper/
├── legiongasper/
│   ├── core/              # Agent, Factory, Captain, Squad, Orchestrator
│   ├── memory/            # 5-layer memory architecture
│   ├── llm/               # Multi-provider LLM router
│   ├── tools/             # Tool registry and built-in tools
│   ├── governance/        # Audit, cost, rate limit, RBAC
│   ├── gateway/           # REST API and WebSocket server
│   ├── dashboard/         # Web dashboard
│   └── cli/               # Command line interface
├── configs/               # Configuration files
├── examples/              # Example scripts
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## 💡 Examples

### Research Squad Example

See `examples/research_squad_example.py` for a complete demonstration of:
- Captain forming a research squad
- Parallel information gathering
- Result aggregation and synthesis

### Code Review Captain Example

See `examples/code_review_captain_example.py` for:
- Captain-led code review process
- Multi-agent analysis (security, style, performance)
- Consolidated review report generation

## 🔧 Advanced Usage

### Custom Agent Templates

```python
from legiongasper.config.agent_templates import AgentTemplate

template = AgentTemplate(
    role="custom_analyst",
    capabilities=["data_analysis", "visualization"],
    tools=["calculator", "file_operations"],
    memory_config={"working_set_size": 50}
)
```

### Tool Development

```python
from legiongasper.tools.registry import ToolRegistry, ToolSchema, ToolParameter

async def my_custom_tool(query: str, limit: int = 10):
    # Your tool logic here
    return {"results": []}

schema = ToolSchema(
    name="my_tool",
    description="Does something useful",
    parameters=[
        ToolParameter(name="query", type="string", description="Search query", required=True),
        ToolParameter(name="limit", type="integer", description="Result limit", required=False)
    ]
)

registry = ToolRegistry()
registry.register(schema, my_custom_tool)
```

### Memory Management

```python
from legiongasper.memory import MemoryManager

manager = MemoryManager()

# Store in different layers
await manager.session.store("key", "value")
await manager.long_term.store("knowledge", {"data": "..."}, importance=0.8)

# Recall with semantic search
results = await manager.long_term.recall("query", top_k=5)
```

## 📊 Monitoring

Access the dashboard at `http://localhost:8080` for:
- Real-time agent status
- Task queue visualization
- Cost analytics
- System health metrics

## 🔐 Security

- **RBAC**: Role-based access control with permissions
- **Audit Logging**: All actions logged with timestamps
- **Rate Limiting**: Token bucket and sliding window algorithms
- **Sandboxed Execution**: Code execution in restricted environment

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- DEATH LEGION Team (DEMO X HEXA)
- OpenClaw Factory Edition

---

**Built with ❤️ by DEATH LEGION Team**
