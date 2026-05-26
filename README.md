<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=44&duration=3000&pause=1000&color=FF2D20&center=true&vCenter=true&width=650&height=90&lines=LEGIONGASPER;DEATH+LEGION+SYSTEM;OpenClaw+Factory+Edition" alt="LEGIONGASPER" />

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=15&duration=2500&pause=900&color=999999&center=true&vCenter=true&width=620&lines=Python+Multi-Agent+System;Captain-Orchestrated+Parallelism;Built+by+DEATH+LEGION+%E2%80%94+DEMO+%C3%97+HEXA" alt="subtitle" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-FF2D20?style=for-the-badge)](LICENSE)
[![Agents](https://img.shields.io/badge/Agents-Parallel-purple?style=for-the-badge&logo=github-actions&logoColor=white)]()
[![Memory](https://img.shields.io/badge/Memory-5--Layer-DAA520?style=for-the-badge)]()

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

</div>

<br/>

## What is this

You give LEGIONGASPER a task. It splits that task into pieces, hands each piece to a specialized agent, runs them in parallel, and stitches the results back together. The captain handles the coordination — you don't.

It runs on FastAPI, comes with a live dashboard at `localhost:8080`, and speaks OpenAI, Anthropic, and OpenRouter without any extra wiring. Memory works across five layers, from what an agent is doing right now down to a ChromaDB vector store that survives reboots.

The honest version: it's not magic. It's a well-structured Python system that solves a real coordination problem — getting multiple LLM agents to work together without you babysitting them.

<div align="center">
<br/>
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2200&pause=600&color=FF2D20&center=true&vCenter=true&width=520&lines=Parallel+agents.+One+brain+running+the+show.;5+memory+layers.+Nothing+gets+forgotten.;Captain+orchestrates.+Squad+executes." alt="taglines" />
<br/><br/>
</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Features

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=17&duration=3500&pause=900&color=FF2D20&center=true&vCenter=true&width=540&lines=%E2%9A%A1+Parallel+Execution;%F0%9F%A7%A0+5-Layer+Memory+Stack;%F0%9F%AB%A1+Captain-Agent+Pattern;%F0%9F%8F%AD+Agent+Factory;%F0%9F%94%80+Multi-Provider+LLM+Router;%F0%9F%94%92+Governance+%26+Audit;%F0%9F%93%A1+Live+WebSocket+Dashboard;%F0%9F%94%8C+REST+%2B+WebSocket+API" alt="features cycling" />

<br/><br/>

<!-- FEATURE CARDS ROW 1 -->
<table>
<tr>

<td align="center" width="280">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd4MHJta2kxMGZxdm1sMW5oZnk5dGx0Z3N4bHZwaGJqNzBwNjFkMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26tn33aiTi1jkl6H6/giphy.gif" width="120" height="80" style="border-radius:8px"/><br/>
<img src="https://img.shields.io/badge/⚡-Parallel%20Execution-FF2D20?style=for-the-badge&labelColor=1a1a1a"/><br/>
<sub>Multiple agents run at the same time. A task that would take 4 minutes sequentially takes 1 minute when four agents split it.</sub>
</td>

<td align="center" width="280">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmFqNWh5dXR5NmZhbW1vNmJsM3RjcXJtdGlxdWloaHh5dGhveWR0NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif" width="120" height="80" style="border-radius:8px"/><br/>
<img src="https://img.shields.io/badge/🧠-5--Layer%20Memory-DAA520?style=for-the-badge&labelColor=1a1a1a"/><br/>
<sub>Session → Working → Daily → Long-term → Collective. Each layer serves a different scope. Nothing bleeds where it shouldn't.</sub>
</td>

<td align="center" width="280">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMmllZGlheTl3a2F6ZTZrbGd1cTFubGZxaXd6OGw4dGJibGxzNHJ2YiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0HlNaQ6gWfllcjDO/giphy.gif" width="120" height="80" style="border-radius:8px"/><br/>
<img src="https://img.shields.io/badge/🫡-Captain--Agent%20Pattern-5B21D8?style=for-the-badge&labelColor=1a1a1a"/><br/>
<sub>One agent takes charge, decomposes the task, forms a squad, and collects results. You don't wire the handoffs manually.</sub>
</td>

</tr>
<tr>

<td align="center" width="280">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcWNodGZ1NmI5YW9ic3RsN2QzeTBsajZveGpuMGZjaGpvbWpkdHJ5eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/du3J3cXyzhj75IOgvA/giphy.gif" width="120" height="80" style="border-radius:8px"/><br/>
<img src="https://img.shields.io/badge/🏭-Agent%20Factory-009688?style=for-the-badge&labelColor=1a1a1a"/><br/>
<sub>Define an agent template once — role, tools, memory config — and spawn as many copies as you need. No copy-pasting setup code.</sub>
</td>

<td align="center" width="280">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbnpnbGlpaHRsMnBxaW51bjdwbGlmeHZheWd4bjc0Y2NhZzB1bHZ0diZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9IgzoKnwFNmISR8I/giphy.gif" width="120" height="80" style="border-radius:8px"/><br/>
<img src="https://img.shields.io/badge/🔀-Multi--Provider%20Router-2563EB?style=for-the-badge&labelColor=1a1a1a"/><br/>
<sub>OpenAI, Anthropic, OpenRouter. Swap providers per agent or per task. The agents don't know and don't care which backend they're hitting.</sub>
</td>

<td align="center" width="280">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmE5dHFxdnk4d2R2aG12c3RtemNiYmZ0YzFtNXdxdWZna2ZnYmt4NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/077i6AULCXc0FKTj9s/giphy.gif" width="120" height="80" style="border-radius:8px"/><br/>
<img src="https://img.shields.io/badge/🔒-Governance%20Layer-DC2626?style=for-the-badge&labelColor=1a1a1a"/><br/>
<sub>Every action gets logged. Every dollar gets tracked. Rate limiting stops agents from going sideways at 3am. RBAC controls who can do what.</sub>
</td>

</tr>
<tr>

<td align="center" width="280">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExamI4aWIwczQ2NTlmbDh2ejVobXlobjRuenBid3NoN3lrZHczZGt3eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9IgG6UmLpFJNZs4w/giphy.gif" width="120" height="80" style="border-radius:8px"/><br/>
<img src="https://img.shields.io/badge/📡-Live%20Dashboard-0EA5E9?style=for-the-badge&labelColor=1a1a1a"/><br/>
<sub>Open <code>localhost:8080</code> and watch what's happening. Active agents, task queue, cost per run — all live, no refresh needed.</sub>
</td>

<td align="center" colspan="2" width="560">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMWk0ZWY0d3Bld3Rkb3VvcDc4dGZ4eDNkYzNod3c5aXV6bXFyaXh1eSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26ufnwz3wDUli7GU0/giphy.gif" width="120" height="80" style="border-radius:8px"/><br/>
<img src="https://img.shields.io/badge/🔌-REST%20%2B%20WebSocket%20API-7C3AED?style=for-the-badge&labelColor=1a1a1a"/><br/>
<sub>Full external API on port 8081. HTTP for control, WebSocket for streaming. Integrate from anything that speaks JSON.</sub>
</td>

</tr>
</table>

</div>

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## System architecture

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2000&pause=800&color=888888&center=true&vCenter=true&width=600&lines=Seven+layers.+One+system.+Zero+babysitting." alt="arch label" />
<br/><br/>
</div>

```
┌─────────────────────────────────────────────────────────────┐
│                    LEGIONGASPER SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│  🔌  Gateway Layer       REST API + WebSocket      :8081    │
├─────────────────────────────────────────────────────────────┤
│  📡  Dashboard Layer     FastAPI + Live Updates    :8080    │
├─────────────────────────────────────────────────────────────┤
│  🫡  Orchestration       Captain → Squad → Queue            │
├─────────────────────────────────────────────────────────────┤
│  🏭  Agent Layer         Factory + Base + Tool Registry     │
├─────────────────────────────────────────────────────────────┤
│  🧠  Memory (5-Tier)     Session/Working/Daily/LTM/CC       │
├─────────────────────────────────────────────────────────────┤
│  🔀  LLM Router          OpenAI / Anthropic / OpenRouter    │
├─────────────────────────────────────────────────────────────┤
│  🔒  Governance          Audit / Cost / Rate Limit / RBAC   │
└─────────────────────────────────────────────────────────────┘
```

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Memory system

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2800&pause=700&color=DAA520&center=true&vCenter=true&width=520&lines=Five+layers.+Each+one+serves+a+different+purpose.;Nothing+gets+forgotten+at+the+wrong+time." alt="memory label" />
<br/><br/>
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM2ZiNnZqbGJubDAxdGZpMmpxcnZ1NzZncjJ1ZGZzYTlhMHptNXF0OCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif" width="180"/>
<br/><br/>
</div>

```
┌─────────────────────────────────────────────────────────────┐
│                    5-LAYER MEMORY STACK                     │
├─────────────────────────────────────────────────────────────┤
│  [1] 🟢 Session Memory        TTL context buffer            │
│         What's happening right now, in this run             │
├─────────────────────────────────────────────────────────────┤
│  [2] 🟡 Working Memory        Priority queue                │
│         Current task focus — what the agent is on          │
├─────────────────────────────────────────────────────────────┤
│  [3] 🟠 Daily Memory          Date-indexed persistence      │
│         What happened today — survives the session         │
├─────────────────────────────────────────────────────────────┤
│  [4] 🔴 Long-term Memory      ChromaDB vector store         │
│         Semantic recall across sessions and reboots        │
├─────────────────────────────────────────────────────────────┤
│  [5] 🟣 Collective Consciousness   Shared agent store       │
│         What the whole squad knows — cross-agent recall    │
└─────────────────────────────────────────────────────────────┘
```

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Quickstart

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=15&duration=2200&pause=700&color=FF2D20&center=true&vCenter=true&width=500&lines=Clone.+Configure.+Run.+That%27s+it." alt="quickstart label" />
<br/><br/>
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMWkwZHZsMTBobXF5cGhuNXZpZXFzY2pyc2txNDF5ZGNhenVsMXY3dSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/QssGEmpkyEOhBCb7e1/giphy.gif" width="150"/>
<br/><br/>
</div>

### 1. Clone and install

```bash
git clone https://github.com/deathlegion/legiongasper.git
cd legiongasper
pip install -r requirements.txt
python -m legiongasper.cli init
```

### 2. Set up `.env`

You need at least one LLM provider key. The rest is optional depending on whether you want distributed memory or vector storage.

```bash
# At minimum, one of these
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key

# If you want distributed memory across workers
REDIS_URL=redis://localhost:6379

# If you want semantic recall to persist
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
```

### 3. Start the server

```bash
# Defaults to :8081 for the API, :8080 for the dashboard
python -m legiongasper.cli serve

# Override ports if something's already running there
python -m legiongasper.cli serve --port 8081 --dashboard-port 8080
```

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## CLI reference

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2000&pause=600&color=888888&center=true&vCenter=true&width=520&lines=legiongasper+%3Ccommand%3E+%5Boptions%5D" alt="cli label" />
<br/><br/>
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdmpzbzE0dWVvaTJmd2Jnb3pwMHc1aTFxb3N2a3hjanZhdWZzMm1mYSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26tn33aiTi1jkl6H6/giphy.gif" width="140"/>
<br/><br/>
</div>

```bash
# First-time setup
legiongasper init

# Spawn an agent from a template
legiongasper agent spawn --template research --id researcher_1

# See what's alive
legiongasper agent list

# Hand off a task
legiongasper task submit "Research quantum computing advances" --priority high

# Check the system is healthy
legiongasper status
```

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## API usage

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2000&pause=700&color=009688&center=true&vCenter=true&width=500&lines=HTTP+on+%3A8081.+WebSocket+for+streaming." alt="api label" />
<br/><br/>
</div>

```python
import requests

# Spawn an agent
requests.post("http://localhost:8081/api/v1/agents/spawn", json={
    "template_id": "research",
    "agent_id": "my_researcher"
})

# Submit a task
requests.post("http://localhost:8081/api/v1/tasks/submit", json={
    "description": "Analyze Python async patterns",
    "priority": "high"
})
```

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Captain-agent pattern

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2500&pause=800&color=5B21D8&center=true&vCenter=true&width=540&lines=One+captain.+Many+agents.+You+stay+out+of+it." alt="captain label" />
<br/><br/>
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGlpMGw0bHpuanR5ZzR5cmFqcmR3M3c5ZnFnNXpxc3F3YXJ0NXZ3biZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0HlNaQ6gWfllcjDO/giphy.gif" width="150"/>
<br/><br/>
</div>

The captain is the only coordination point. It breaks a task apart, figures out which agents should handle which pieces, runs them in parallel, and merges the output. You interact with the captain — not with each agent directly.

```python
captain = Captain(agent_id="research_lead")

# One task becomes many subtasks
subtasks = captain.decompose_task("Analyze market trends")

# Subtasks become a squad
squad = captain.form_squad(subtasks)

# Squad runs — you wait
results = await squad.execute_parallel()

# Captain merges everything
final = captain.aggregate_results(results)
```

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Extending the system

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2000&pause=600&color=FF2D20&center=true&vCenter=true&width=520&lines=Custom+templates.+Custom+tools.+Direct+memory+access." alt="extend label" />
<br/><br/>
</div>

### Custom agent templates

```python
from legiongasper.config.agent_templates import AgentTemplate

template = AgentTemplate(
    role="custom_analyst",
    capabilities=["data_analysis", "visualization"],
    tools=["calculator", "file_operations"],
    memory_config={"working_set_size": 50}
)
```

### Custom tools

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

ToolRegistry().register(schema, my_custom_tool)
```

### Memory access

```python
from legiongasper.memory import MemoryManager

manager = MemoryManager()

await manager.session.store("key", "value")
await manager.long_term.store("knowledge", {"data": "..."}, importance=0.8)

# Semantic recall — searches by meaning, not exact key
results = await manager.long_term.recall("query", top_k=5)
```

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Project structure

```
legiongasper/
├── legiongasper/
│   ├── core/          # Agent, Factory, Captain, Squad, Orchestrator
│   ├── memory/        # 5-layer memory stack
│   ├── llm/           # Multi-provider router
│   ├── tools/         # Tool registry + built-ins
│   ├── governance/    # Audit, cost, rate limiting, RBAC
│   ├── gateway/       # REST + WebSocket server
│   ├── dashboard/     # Live web UI
│   └── cli/           # Command line interface
├── configs/
├── examples/
├── requirements.txt
└── README.md
```

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Examples

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMng3aTB3dXM0NW5vNm50aTd5MG9jcml2dTlzZjVnNXp5dng3bjF6eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9IgzoKnwFNmISR8I/giphy.gif" width="150"/>
<br/><br/>
</div>

**`examples/research_squad_example.py`** — A captain forms a research squad, agents run in parallel, and the results combine into a single report. Good starting point if you're new to the captain-agent flow.

**`examples/code_review_captain_example.py`** — Captain-led code review where three agents audit security, style, and performance independently. The captain merges their findings into one report. Useful to see how agents with different specializations coordinate.

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Dashboard

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2000&pause=700&color=0EA5E9&center=true&vCenter=true&width=500&lines=localhost%3A8080+%E2%80%94+open+it+while+things+run" alt="dashboard label" />
<br/><br/>
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExamI4aWIwczQ2NTlmbDh2ejVobXlobjRuenBid3NoN3lrZHczZGt3eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9IgG6UmLpFJNZs4w/giphy.gif" width="160"/>
<br/><br/>
</div>

Open `http://localhost:8080` while the server runs. It shows which agents are active, what they're working on, task queue depth, completion rates, and cost per provider, agent, and task. All live — no polling, no refresh.

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Security

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=2000&pause=700&color=DC2626&center=true&vCenter=true&width=500&lines=Agents+are+powerful.+Governance+keeps+them+in+check." alt="security label" />
<br/><br/>
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmE5dHFxdnk4d2R2aG12c3RtemNiYmZ0YzFtNXdxdWZna2ZnYmt4NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/077i6AULCXc0FKTj9s/giphy.gif" width="140"/>
<br/><br/>
</div>

| | |
|---|---|
| 🔐 **RBAC** | Users and agents get roles. Roles get permissions. An agent can only do what its role allows. |
| 📋 **Audit logging** | Every action is recorded. You can trace what any agent did, when, and at what cost. |
| 🚦 **Rate limiting** | Prevents agents from running wild. Especially useful in long-running or unattended jobs. |
| 📦 **Sandboxed execution** | Code runs isolated. One agent going sideways doesn't take the others down. |

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<br/>

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR. Issues and discussions are open.

<br/>

---

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=22&duration=3000&pause=1000&color=FF2D20&center=true&vCenter=true&width=500&lines=Built+by+DEATH+LEGION;DEMO+%C3%97+HEXA;OpenClaw+Factory+Edition" alt="footer" />

<br/>

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMWk0ZWY0d3Bld3Rkb3VvcDc4dGZ4eDNkYzNod3c5aXV6bXFyaXh1eSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26ufnwz3wDUli7GU0/giphy.gif" width="200"/>

<br/><br/>

[![MIT License](https://img.shields.io/badge/License-MIT-FF2D20?style=for-the-badge)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-22c55e?style=for-the-badge)](CONTRIBUTING.md)

<br/>

*Made with care, by DEATH LEGION Team*

<br/>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

</div>
