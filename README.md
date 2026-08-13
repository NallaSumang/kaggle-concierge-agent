<div align="center">
  <h1>🤖 Kaggle Concierge Agent</h1>
  <p>An autonomous, self-healing file-system organizer powered by Google ADK 2.6 and Gemini.</p>
</div>

---

## 📖 Overview

**Kaggle Concierge Agent** is a state-of-the-art local CLI agent built with Google's **Agent Development Kit (ADK) 2.6**. It acts as an autonomous workspace concierge, utilizing the **Model Context Protocol (MCP)** to interact with your local filesystem via Natural Language.

Far beyond a simple LLM wrapper, this system boasts **Enterprise-Grade Graceful Degradation**. If cloud APIs rate-limit, crash, or lose authentication, the agent instantly hot-swaps to a secure, deterministic offline heuristic engine—ensuring zero downtime. It also features a globally unified **Undo Architecture**, allowing users to instantly revert massive file migrations with a single command.

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  ADK 2.6.3 CLI Runtime                                      │
│                                                             │
│  [ CLI Interceptor ] ──( "undo" )──> Transaction Reverter   │
│          │                                                  │
│  ┌───────▼────────────────────────────────────────────────┐ │
│  │  LlmAgent ("file_organizer")                           │ │
│  │   model: gemini-2.5-flash                              │ │
│  │   tools:                                               │ │
│  │     └─ MCPToolset ──stdio──> @modelcontextprotocol     │ │
│  │                              /server-filesystem        │ │
│  └───────┬────────────────────────────────────────────────┘ │
│          │                                                  │
│  [ Error Boundary: 429 / 503 / Missing API Key ]            │
│          │                                                  │
│  ┌───────▼────────────────────────────────────────────────┐ │
│  │  Offline Graceful Degradation Engine                   │ │
│  │   - Regex-based extension heuristics                   │ │
│  │   - Fallback tabular formatting                        │ │
│  │   - Synchronous fallback execution                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Core Capabilities

### 1. Natural Language Organization (Online)
Utilizing Gemini 2.5 Flash, you can simply type `"Can you clean up this absolute mess?"` and the AI will intuitively plan category structures, extract semantic meaning from file names, and reorganize the workspace via the MCP Filesystem server.

### 2. Zero-Downtime Offline Fallback (Offline)
If you hit a Google API Free Tier limit (`429 RESOURCE_EXHAUSTED`), lose internet (`503`), or lack a `.env` key, the script **does not crash**. It instantly catches the exception and falls back to a deterministic, regex-based categorization engine that mimics the LLM's tabular approval UI perfectly.

### 3. Global Undo Architecture
AI Hallucinations are dangerous in filesystem management. Every file move (both LLM and Offline) writes a deterministic transaction log to `.move_history.json`. Typing `undo` intercepts the LLM, reads the log, and precisely reverts hundreds of files back to their original state in milliseconds.

### 4. Human-in-the-Loop Execution
No files are ever touched without explicit consent. Both the Online Agent and the Offline Engine will halt execution, render a detailed tabular plan of proposed moves, and await a strict `(Y/N)` user approval before invoking `shutil.move()`.

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Agent Framework** | Google ADK 2.6.3 |
| **LLM** | Gemini 2.5 Flash |
| **Tool Protocol** | Model Context Protocol (MCP < 2.0.0) |
| **MCP Transport** | stdio (auto-launched via `npx`) |
| **Environment** | Python 3.11+, local `venv` containment |

## 🚀 Getting Started

### 1. Environment Setup
You **must** use the localized virtual environment to prevent `pydantic` and `mcp` global namespace collisions.
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=<your-gemini-api-key>
AGENT_WORKSPACE=./workspace
```

### 3. Execution
Run the conversational interface:
```powershell
python agent.py
```
* **To trigger AI sorting:** `"organize my workspace"`
* **To revert the last action:** `"undo"`
* **To force offline mode:** Remove your API key and type `"organize"`
