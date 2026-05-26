<div align="center">

<!-- Animated banner using SVG -->
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=40&duration=3000&pause=1000&color=FF2D20&center=true&vCenter=true&width=600&height=80&lines=LEGIONGASPER;DEATH+LEGION+SYSTEM;OpenClaw+Factory+Edition" alt="LEGIONGASPER" />

<br/>

<!-- Animated subheading -->
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=16&duration=2500&pause=800&color=888888&center=true&vCenter=true&width=600&lines=Python+Multi-Agent+System;Captain-Orchestrated+Parallelism;Built+by+DEATH+LEGION+%E2%80%94+DEMO+%C3%97+HEXA" alt="subtitle" />

<br/><br/>

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-FF2D20?style=for-the-badge)](LICENSE)
[![Agents](https://img.shields.io/badge/Agents-Parallel-purple?style=for-the-badge&logo=github-actions&logoColor=white)]()
[![Memory](https://img.shields.io/badge/Memory-5--Layer-gold?style=for-the-badge)]()

<br/>

<!-- Animated divider -->
<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

</div>

<br/>

## What Is This

LEGIONGASPER is a multi-agent orchestration system. You give it a task, it breaks that task apart, farms the pieces out to specialized agents running in parallel, and reassembles the results. The captain-agent pattern means one agent coordinates the others rather than you doing it manually.

It's built on FastAPI, ships with a real-time dashboard, and supports OpenAI, Anthropic, and OpenRouter out of the box. Memory works in five layers — from in-session context all the way down to a ChromaDB vector store that persists across runs.

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2000&pause=500&color=FF2D20&center=true&vCenter=true&width=500&lines=Parallel+Agents+%E2%80%94+One+Brain;5+Memory+Layers+%E2%80%94+Zero+Amnesia;Captain+Orchestrates+%E2%80%94+Squad+Executes" alt="features typing" />
</div>

<br/>

---

## Features

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=18&duration=4000&pause=1000&color=FF2D20&center=true&vCenter=true&width=500&lines=%E2%9A%A1+Parallel+Execution;%F0%9F%A7%A0+5-Layer+Memory;%F0%9F%AB%A1+Captain+Pattern;%F0%9F%8F%AD+Factory+Spawning;%F0%9F%94%92+Governance+Layer;%F0%9F%93%A1+Live+Dashboard" alt="features" />
</div>

<br/>

| Feature | What It Does |
|---|---|
| ⚡ **Parallel Execution** | Multiple agents run at the same time. Tasks that would block sequentially don't block here. |
| 🧠 **5-Layer Memory** | Session → Working → Daily → Long-term → Collective. Agents remember what matters at the right scope. |
| 🫡 **Captain-Agent Pattern** | One agent decomposes the task, forms a squad, and aggregates results. You don't wire the coordination yourself. |
| 🏭 **Agent Factory** | Agents spawn from templates. Define the role, capabilities, and toolset once; reuse everywhere. |
| 🔀 **Multi-Provider Router** | OpenAI, Anthropic, OpenRouter — swap providers per-agent or per-task without touching agent code. |
| 🔒 **Governance Layer** | Audit logs, cost tracking, rate limiting, and RBAC. You know what your agents spent and did. |
| 📡 **Live Dashboard** | Hit `localhost:8080` and watch agents work in real time. |
| 🔌 **REST + WebSocket** | Full external API on port 8081. Integrate from anything. |

<br/>

---

## System Architecture

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=16&duration=2000&pause=800&color=888888&center=true&vCenter=true&width=600&lines=Seven+layers.+One+system." alt="arch" />
</div>

```
┌─────────────────────────────────────────────────────────────┐
│                    LEGIONGASPER SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│  Gateway Layer        REST API + WebSocket   :8081          │
├─────────────────────────────────────────────────────────────┤
│  Dashboard Layer      FastAPI + Live Updates  :8080          │
├─────────────────────────────────────────────────────────────┤
│  Orchestration        Captain → Squad → Queue               │
├─────────────────────────────────────────────────────────────┤
│  Agent Layer          Factory + Base Agent + Tool Registry  │
├─────────────────────────────────────────────────────────────┤
│  Memory (5-Tier)      Session / Working / Daily / LTM / CC  │
├─────────────────────────────────────────────────────────────┤
│  LLM Router           OpenAI / Anthropic / OpenRouter       │
├─────────────────────────────────────────────────────────────┤
│  Governance           Audit / Cost / Rate Limit / RBAC      │
└─────────────────────────────────────────────────────────────┘
```

<br/>

---

## Memory System

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=15&duration=3000&pause=600&color=gold&center=true&vCenter=true&width=500&lines=Five+layers.+Nothing+forgotten." alt="memory" />
</div>

```
┌─────────────────────────────────────────────────────────────┐
│                    5-LAYER MEMORY STACK                     │
├─────────────────────────────────────────────────────────────┤
│  [1] Session Memory        TTL context buffer               │
│      → What's happening right now in this run              │
├─────────────────────────────────────────────────────────────┤
│  [2] Working Memory        Priority queue                   │
│      → Current task focus, active state                    │
├─────────────────────────────────────────────────────────────┤
│  [3] Daily Memory          Date-indexed persistence         │
│      → What happened today                                 │
├─────────────────────────────────────────────────────────────┤
│  [4] Long-term Memory      ChromaDB vector store            │
│      → Semantic recall across sessions                     │
├─────────────────────────────────────────────────────────────┤
│  [5] Collective Consciousness   Shared agent knowledge      │
│      → What the whole squad knows                          │
└─────────────────────────────────────────────────────────────┘
```

<br/>

---

## Quickstart

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=16&duration=2500&pause=700&color=FF2D20&center=true&vCenter=true&width=500&lines=Clone.+Configure.+Run." alt="quickstart" />
</div>

### 1. Clone and Install

```bash
git clone https://github.com/deathlegion/legiongasper.git
cd legiongasper
pip install -r requirements.txt
python -m legiongasper.cli init
```

### 2. Configure `.env`

```bash
# Required — at least one LLM provider
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional — distributed memory
REDIS_URL=redis://localhost:6379

# Optional — vector storage
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
```

### 3. Start the Server

```bash
# Default ports
python -m legiongasper.cli serve

# Custom ports
python -m legiongasper.cli serve --port 8081 --dashboard-port 8080
```

<br/>

---

## CLI Reference

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=15&duration=2000&pause=600&color=888888&center=true&vCenter=true&width=500&lines=legiongasper+%3Ccommand%3E" alt="cli" />
</div>

```bash
# Initialize config
legiongasper init

# Spawn an agent from a template
legiongasper agent spawn --template research --id researcher_1

# See what's running
legiongasper agent list

# Submit a task
legiongasper task submit "Research quantum computing advances" --priority high

# System health
legiongasper status
```

<br/>

---

## API Usage

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

<br/>

---

## Captain-Agent Pattern

This is the core coordination primitive. A captain agent breaks a task into subtasks, forms a squad, runs them in parallel, and aggregates the results. You don't manage the individual agents — the captain does.

```python
captain = Captain(agent_id="research_lead")

# Task → subtasks
subtasks = captain.decompose_task("Analyze market trends")

# Subtasks → squad
squad = captain.form_squad(subtasks)

# Squad → parallel execution
results = await squad.execute_parallel()

# Results → single output
final = captain.aggregate_results(results)
```

<br/>

---

## Extending the System

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

### Custom Tools

```python
from legiongasper.tools.registry import ToolRegistry, ToolSchema, ToolParameter

async def my_custom_tool(query: str, limit: int = 10):
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

### Memory Access

```python
from legiongasper.memory import MemoryManager

manager = MemoryManager()

await manager.session.store("key", "value")
await manager.long_term.store("knowledge", {"data": "..."}, importance=0.8)

# Semantic recall
results = await manager.long_term.recall("query", top_k=5)
```

<br/>

---

## Project Structure

```
legiongasper/
├── legiongasper/
│   ├── core/          # Agent, Factory, Captain, Squad, Orchestrator
│   ├── memory/        # 5-layer memory stack
│   ├── llm/           # Multi-provider router
│   ├── tools/         # Tool registry and built-ins
│   ├── governance/    # Audit, cost, rate limiting, RBAC
│   ├── gateway/       # REST + WebSocket
│   ├── dashboard/     # Live web UI
│   └── cli/           # Command line
├── configs/
├── examples/
├── requirements.txt
└── README.md
```

<br/>

---

## Examples

**`examples/research_squad_example.py`** — Captain forms a research squad, agents run in parallel, results combine into a single report.

**`examples/code_review_captain_example.py`** — Captain-led code review. Three agents audit security, style, and performance independently. Captain merges the findings.

<br/>

---

## Dashboard

Open `http://localhost:8080` after starting the server. You'll see:

- Which agents are active and what they're doing
- Task queue depth and completion rates
- Cost per provider, per agent, per task
- System health at a glance

<br/>

---

## Security

- **RBAC** — users and agents get roles; roles get permissions
- **Audit Logging** — every agent action is recorded
- **Rate Limiting** — prevents runaway execution
- **Sandboxed Execution** — code runs isolated

<br/>

---

<div align="center">

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=20&duration=3000&pause=1000&color=FF2D20&center=true&vCenter=true&width=500&lines=Built+by+DEATH+LEGION;DEMO+%C3%97+HEXA;OpenClaw+Factory+Edition" alt="footer" />

<br/><br/>

[![MIT License](https://img.shields.io/badge/License-MIT-FF2D20?style=for-the-badge)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen?style=for-the-badge)](CONTRIBUTING.md)

<br/>

*Made with care, by DEATH LEGION Team*

</div>
