<div align="center">
  <h1>🤖 Kaggle Concierge Agent</h1>
  <p>An autonomous file-system organizer powered by Google ADK 2.0 and Gemini.</p>
</div>

---

## 📖 Overview

**Kaggle Concierge Agent** is a local CLI agent built with Google's **Agent Development Kit (ADK) 2.0** Workflow API. It connects to a local **MCP Filesystem Server** to automatically scan, categorize, and organize files in a workspace directory — with a strict human-in-the-loop approval step before any file is moved.

## 🏗️ System Architecture

```text
┌──────────────────────────────────────────────────────────┐
│  ADK 2.0 Workflow Runtime                                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  LlmAgent  ("file_organizer")                       │ │
│  │   model : gemini-2.5-flash                          │ │
│  │   tools :                                           │ │
│  │     └─ MCPToolset ──stdio──▶ @modelcontextprotocol  │ │
│  │                              /server-filesystem     │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Workflow Graph                                     │ │
│  │   START ──▶ file_organizer ──▶ END                  │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

The agent follows a strict **human-in-the-loop** workflow:

1. **SCAN** — Reads the workspace directory and inventories every file with metadata (name, size, type).
2. **PLAN** — Proposes a sorting plan: which file should move to which subfolder, and why.
3. **CONFIRM** — Waits for explicit user approval (Y/N) before moving anything. No file is touched without consent.

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Agent Framework** | Google ADK 2.0 (Workflow API) |
| **LLM** | Gemini 2.5 Flash (via `GOOGLE_API_KEY`) |
| **Tool Protocol** | Model Context Protocol (MCP) — Filesystem Server |
| **MCP Transport** | stdio (auto-launched via `npx`) |
| **Session Management** | `InMemorySessionService` (ephemeral) |
| **Language** | Python 3.11+ |

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js / `npx` (for the MCP filesystem server)

### Run
```bash
pip install -r requirements.txt
python agent.py
```

Or use the ADK Web UI:
```bash
adk web agent.py
```

### Environment Variables
Create a `.env` file:
```env
GOOGLE_API_KEY=<your-gemini-api-key>
AGENT_WORKSPACE=<path-to-target-directory>   # defaults to ./workspace
AGENT_MODEL=gemini-2.5-flash                 # optional override
```

The MCP server is started automatically as a subprocess via stdio — no manual setup required.

## 📜 License
Distributed under the MIT License.
