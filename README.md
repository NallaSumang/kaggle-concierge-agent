# 🗂️ Smart Local File Organizer (Concierge Agent)

An intelligent, completely local file organization assistant built for the **Kaggle 5-Day AI Agents Capstone Project**. 

This Concierge Agent solves the universal problem of digital clutter by securely scanning, categorizing, and sorting local files based on their extensions. It is designed with a strict human-in-the-loop workflow and features graceful offline degradation to ensure reliability even when API rate limits are hit.

## 🚀 Key Course Concepts Applied

This project explicitly demonstrates four core concepts taught in the 5-Day Intensive Vibe Coding Course:

1. **Agent Development Kit (ADK 2.0):** The core logic is orchestrated using Google's `LlmAgent` and `Runner` from the ADK 2.0 library. It includes a custom exception handler that gracefully degrades to local deterministic heuristics if the Gemini API encounters a `429 Quota Exceeded` error.
2. **MCP Server Integration:** The agent uses the `@modelcontextprotocol/server-filesystem` MCP toolset. This sandboxes the agent, giving it strict, scoped access to list directories and move files without requiring custom Python OS integration.
3. **Security Features (Human-In-The-Loop):** The agent operates under a strict "Scan & Plan" paradigm. It is physically prohibited from moving, deleting, or altering any file until it presents a summary table to the user and receives explicit `Y/N` terminal approval.
4. **Antigravity IDE:** The initial boilerplate and structural logic were generated using prompt-driven "vibe coding" within Google's Antigravity IDE environment.

## 🛠️ Architecture Pipeline

The agent uses a purely local, secure pipeline:
`User CLI` ➔ `ADK 2.0 Runner` ➔ `Gemini 2.5 Flash` ➔ `File System MCP Server` ➔ `Local Workspace`

## 💻 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/NallaSumang/kaggle-concierge-agent.git](https://github.com/NallaSumang/kaggle-concierge-agent.git)
   cd kaggle-concierge-agent
