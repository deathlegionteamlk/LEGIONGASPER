# LEGIONGASPER - Autonomous Agent Framework
## "OpenClaw Factory Edition" - Parallel Agent Architecture with Captain Orchestration

### Research Summary
**OpenClaw Analysis:**
- OpenClaw uses Markdown-as-Config with Gateway daemon architecture
- 4-layer memory: Session, Daily, Long-term, Shared
- Hierarchical delegation but limited true parallelism
- Single-threaded agent execution with sub-agent spawning
- Self-hosted, multi-channel gateway approach

**LEGIONGASPER Improvements Over OpenClaw:**
1. **True Parallel Execution** - Async/await based agent squads running concurrently
2. **Captain-Agent Pattern** - Captains receive tasks, distribute to parallel agent workers
3. **Factory Pattern** - Dynamic agent spawning with configurable templates
4. **Advanced 5-Layer Memory** - Adds "Collective Consciousness" layer for cross-squad learning
5. **Built-in Governance** - Rate limiting, cost tracking, audit logging by default
6. **Multi-Provider LLM Routing** - Intelligent model selection based on task complexity
7. **Company/Enterprise Mode** - Team hierarchies, access control, resource quotas

---

## Goal
Build LEGIONGASPER - a production-grade autonomous agent framework that surpasses OpenClaw with true parallel execution, captain-based orchestration, and factory-pattern agent management. Coded by DEATH LEGION Team (DEMO X HEXA).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LEGIONGASPER GATEWAY                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   CAPTAIN   │  │   CAPTAIN   │  │   CAPTAIN   │  ...         │
│  │   ALPHA     │  │   BETA      │  │   GAMMA     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                 │                 │                     │
│    ┌────┴────┐       ┌────┴────┐       ┌────┴────┐              │
│    │ AGENT   │       │ AGENT   │       │ AGENT   │              │
│    │ SQUAD   │       │ SQUAD   │       │ SQUAD   │              │
│    │ (parallel)│      │ (parallel)│      │ (parallel)│           │
│    └─────────┘       └─────────┘       └─────────┘              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              COLLECTIVE CONSCIOUSNESS LAYER              │   │
│  │         (Cross-squad learning & knowledge sharing)        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Subtasks

### Phase 1: Core Infrastructure

1. **Setup Project Structure & Dependencies**
   - Create modular Python package structure
   - Install: asyncio, pydantic, openai, anthropic, openrouter-python, chromadb, redis, fastapi, uvicorn, structlog, prometheus-client
   - Setup logging, configuration management
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/` package structure

2. **Build Configuration System (YAML-based, superior to OpenClaw's Markdown)**
   - Agent factory templates (YAML configs)
   - Captain role definitions
   - Squad composition rules
   - Multi-provider LLM routing config
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/config/` with YAML schemas

3. **Implement 5-Layer Memory Architecture**
   - Layer 1: Session (ephemeral, per-conversation)
   - Layer 2: Working (task-specific, short-term)
   - Layer 3: Daily (persistent daily summaries)
   - Layer 4: Long-term (vector DB embeddings)
   - Layer 5: Collective Consciousness (cross-squad knowledge graph)
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/memory/` with all 5 layers

### Phase 2: Agent Core

4. **Build Base Agent Class with Async Support**
   - Async/await execution model
   - Tool registry and execution
   - State management
   - Event streaming
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/core/agent.py`

5. **Implement Agent Factory Pattern**
   - Dynamic agent spawning from templates
   - Agent pooling and lifecycle management
   - Resource allocation and quotas
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/core/factory.py`

6. **Create Multi-Provider LLM Router**
   - OpenAI, Anthropic, OpenRouter integration
   - Model tier selection (nano/mid/flagship)
   - Cost tracking and rate limiting
   - Fallback handling
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/llm/router.py`

### Phase 3: Captain-Agent Orchestration

7. **Build Captain Class**
   - Task decomposition and planning
   - Squad formation and assignment
   - Result aggregation and synthesis
   - Progress monitoring
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/core/captain.py`

8. **Implement Parallel Agent Squad Execution**
   - Asyncio-based parallel task execution
   - Semaphore-based concurrency control
   - Inter-agent communication within squads
   - Result collation patterns (reduce, merge, vote)
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/core/squad.py`

9. **Create Task Orchestration Engine**
   - Task queue management
   - Priority scheduling
   - Dependency resolution
   - Expected output: `/app/legiongasper_framework_0813/legiongasper/core/orchestrator.py`

### Phase 4: Tools & Capabilities

10. **Build Tool System**
    - Tool schema definition (JSON Schema)
    - Built-in tools: web_search, code_execution, file_operations, api_call
    - Tool permission system
    - Expected output: `/app/legiongasper_framework_0813/legiongasper/tools/` with registry and built-ins

11. **Implement Code Execution Sandbox**
    - Docker-based sandbox for code execution
    - Resource limits (CPU, memory, time)
    - Expected output: `/app/legiongasper_framework_0813/legiongasper/tools/sandbox.py`

### Phase 5: Enterprise Features

12. **Build Governance & Monitoring**
    - Audit logging (all agent actions)
    - Cost tracking per agent/captain/team
    - Rate limiting (requests per minute, tokens per day)
    - Access control (RBAC)
    - Expected output: `/app/legiongasper_framework_0813/legiongasper/governance/` with audit, costs, limits

13. **Create Web Dashboard (FastAPI + WebSocket)**
    - Real-time agent monitoring
    - Captain squad visualization
    - Cost and usage analytics
    - Task queue viewer
    - Expected output: `/app/legiongasper_framework_0813/legiongasper/dashboard/` with API and UI

### Phase 6: Integration & Deployment

14. **Build Gateway Server**
    - FastAPI-based API gateway
    - WebSocket for real-time updates
    - REST endpoints for task submission
    - Multi-channel support (web, API, CLI)
    - Expected output: `/app/legiongasper_framework_0813/legiongasper/gateway/server.py`

15. **Create CLI Interface**
    - Agent management commands
    - Captain task submission
    - Configuration management
    - Monitoring commands
    - Expected output: `/app/legiongasper_framework_0813/legiongasper/cli/main.py`

16. **Write Documentation & Examples**
    - README with architecture overview
    - Quickstart guide
    - Example: Research squad with multiple agents
    - Example: Code review captain with parallel reviewers
    - Expected output: `/app/legiongasper_framework_0813/README.md`, `/app/legiongasper_framework_0813/examples/`

---

## Deliverables

| File Path | Description |
|-----------|-------------|
| `/app/legiongasper_framework_0813/legiongasper/` | Main Python package |
| `/app/legiongasper_framework_0813/legiongasper/core/` | Agent, Captain, Squad, Factory, Orchestrator |
| `/app/legiongasper_framework_0813/legiongasper/memory/` | 5-layer memory system |
| `/app/legiongasper_framework_0813/legiongasper/llm/` | Multi-provider LLM router |
| `/app/legiongasper_framework_0813/legiongasper/tools/` | Tool registry and built-ins |
| `/app/legiongasper_framework_0813/legiongasper/governance/` | Audit, costs, rate limits |
| `/app/legiongasper_framework_0813/legiongasper/gateway/` | API server and WebSocket |
| `/app/legiongasper_framework_0813/legiongasper/dashboard/` | Web dashboard |
| `/app/legiongasper_framework_0813/legiongasper/cli/` | Command-line interface |
| `/app/legiongasper_framework_0813/configs/` | Example configurations |
| `/app/legiongasper_framework_0813/examples/` | Usage examples |
| `/app/legiongasper_framework_0813/README.md` | Documentation |
| `/app/legiongasper_framework_0813/requirements.txt` | Dependencies |

---

## Evaluation Criteria

- [ ] Framework starts without errors
- [ ] Can spawn agents from factory templates
- [ ] Captain can distribute tasks to parallel agent squads
- [ ] All 5 memory layers functional
- [ ] Multi-provider LLM routing works
- [ ] Tool execution with permissions
- [ ] Audit logging captures all actions
- [ ] Dashboard displays real-time agent status
- [ ] CLI commands functional
- [ ] Example scripts run successfully

---

## Notes

- **Team**: DEATH LEGION (DEMO X HEXA)
- **Target**: Surpass OpenClaw with true parallelism and captain-agent architecture
- **License**: MIT (same as OpenClaw)
- **Deployment**: Self-hosted, Docker-ready
- **Public URLs**: 
  - Frontend: http://1b2dcce4-299f-40b6-ab01-9b94ccd45945.heyneo.so/pV8tkPgOgiO1hVq3u6kbfV9wwIIoOm8M/application/
  - Backend: http://1b2dcce4-299f-40b6-ab01-9b94ccd45945.heyneo.so/pV8tkPgOgiO1hVq3u6kbfV9wwIIoOm8M/bknd/
