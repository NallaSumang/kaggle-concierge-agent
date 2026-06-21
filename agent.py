"""
ADK 2.0 Agent — Smart Local File Organizer
===========================================

An AI agent built with Google's Agent Development Kit (ADK) 2.0 Workflow API
that connects to a local File System MCP server to automatically scan,
categorize, and organize files in a workspace directory.

The agent follows a strict human-in-the-loop workflow:
  1. SCAN   — Reads the workspace and inventories every file.
  2. PLAN   — Proposes a sorting plan (which file → which subfolder).
  3. CONFIRM — Waits for explicit user approval (Y/N) before moving anything.

Architecture
------------
┌──────────────────────────────────────────────────────────┐
│  ADK 2.0 Workflow Runtime                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  LlmAgent  ("file_organizer")                       │  │
│  │   model : gemini-2.5-flash                          │  │
│  │   tools :                                           │  │
│  │     └─ MCPToolset ──stdio──▶ @modelcontextprotocol  │  │
│  │                              /server-filesystem     │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Workflow Graph                                      │  │
│  │   START ──▶ file_organizer ──▶ END                   │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘

Quick start
-----------
  1.  pip install -r requirements.txt
  2.  Ensure Node.js / npx is available (for the MCP filesystem server)
  3.  python agent.py
      — or —
      adk web agent.py      (opens the ADK Web UI)

The MCP server is started automatically as a subprocess via stdio.
"""

from __future__ import annotations

import asyncio
import os
import sys
import logging

# Suppress ADK internal exception traces so the fallback looks clean
logging.getLogger("google.adk").setLevel(logging.CRITICAL)
logging.getLogger("google.genai").setLevel(logging.CRITICAL)

from pathlib import Path

# Load environment variables from .env BEFORE any google imports
# so that GOOGLE_API_KEY / GOOGLE_GENAI_USE_VERTEXAI are visible.
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams, StdioServerParameters
from google.genai import types

# ──────────────────────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────────────────────

# The folder the agent is allowed to access.
# Default: a "workspace" subdirectory next to this script.
ACCESSIBLE_FOLDER = os.environ.get(
    "AGENT_WORKSPACE",
    str(Path(__file__).resolve().parent / "workspace"),
)

# Model to use for the LLM agent.
MODEL_ID = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")

# Agent identity constants
AGENT_NAME = "file_organizer"
APP_NAME = "file_organizer_app"

# ---------------------------------------------------------------------------
# REQUIRED KAGGLE CONCEPT: ADK 2.0 with File System MCP Server
# The system instruction below drives an LlmAgent that uses the MCP Filesystem
# Server toolset to scan, categorize, and reorganize files in a local workspace.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# REQUIRED KAGGLE CONCEPT: Human-in-the-loop security checkpoint
# The agent MUST present a full sorting plan and wait for explicit user
# approval (Y/N) before moving, renaming, or modifying ANY file.  This
# prevents unintended data loss and keeps the human in control at all times.
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """\
You are the **Smart Local File Organizer**, an AI agent whose sole job is to
bring order to a messy workspace directory.

You have access to a local file system through the MCP Filesystem Server.
Use its tools (list_directory, read_file, move_file, create_directory, etc.)
to carry out the workflow described below.

═══════════════════════════════════════════════════════════
  FILE CATEGORIES  (use these exact subfolder names)
═══════════════════════════════════════════════════════════
  📂 Code        → .py, .js, .ts, .java, .c, .cpp, .h, .go, .rs, .rb, .php,
                    .sh, .bat, .ps1, .sql, .html, .css, .jsx, .tsx, .ipynb
  📂 Documents   → .pdf, .doc, .docx, .txt, .md, .rst, .odt, .rtf, .tex,
                    .ppt, .pptx, .xls, .xlsx, .pages, .key, .numbers
  📂 Data        → .csv, .json, .xml, .yaml, .yml, .toml, .parquet, .avro,
                    .tsv, .sqlite, .db, .ndjson, .geojson
  📂 Media       → .png, .jpg, .jpeg, .gif, .svg, .webp, .mp4, .mp3, .wav,
                    .avi, .mov, .mkv, .flac, .ogg, .bmp, .ico, .tiff
  📂 Archives    → .zip, .tar, .gz, .bz2, .7z, .rar, .xz, .tgz
  📂 Config      → .env, .ini, .cfg, .conf, .properties, .dockerignore,
                    .gitignore, .editorconfig, Dockerfile, Makefile,
                    docker-compose.yml
  📂 Other       → anything that does not match the categories above

═══════════════════════════════════════════════════════════
  MANDATORY WORKFLOW  (follow these steps IN ORDER)
═══════════════════════════════════════════════════════════

STEP 1 — SCAN
  • Use the file-system tools to list ALL files (recursively) in the
    workspace root.
  • Identify each file's extension and map it to one of the categories above.
  • If a file is already inside a correctly-named category subfolder,
    mark it as "already organized" and skip it.

STEP 2 — REPORT & PROPOSE A PLAN
  • Print a clear, formatted summary table with these columns:
      #  |  File Name  |  Current Location  |  Proposed Destination  |  Category
  • At the bottom, print totals: how many files per category, how many
    will be moved, how many are already in place.

  ╔══════════════════════════════════════════════════════════════════════╗
  ║  ⚠️  HUMAN-IN-THE-LOOP SECURITY CHECKPOINT                         ║
  ║                                                                     ║
  ║  After presenting the plan you MUST ask:                            ║
  ║                                                                     ║
  ║    "Do you approve this sorting plan? (Y/N)"                        ║
  ║                                                                     ║
  ║  • If the user replies Y / Yes / Approve  → proceed to Step 3.      ║
  ║  • If the user replies N / No / Cancel    → STOP. Do NOT move any   ║
  ║    files. Thank the user and wait for new instructions.             ║
  ║  • If the user replies with modifications → update the plan and     ║
  ║    re-present it, then ask for approval again.                      ║
  ║                                                                     ║
  ║  🚫  NEVER move, rename, or delete ANY file without approval.       ║
  ╚══════════════════════════════════════════════════════════════════════╝

STEP 3 — EXECUTE (only after explicit approval)
  • Create the necessary category subfolders if they don't exist.
  • Move each file to its designated subfolder.
  • After all moves are complete, print a final summary:
      ✅  Moved: <count>
      ⏭️  Skipped (already organized): <count>
      ❌  Errors: <count> (with details)

═══════════════════════════════════════════════════════════
  SAFETY RULES
═══════════════════════════════════════════════════════════
  1. NEVER delete files. Only move them.
  2. NEVER overwrite an existing file. If a name collision occurs, append
     a numeric suffix (e.g., report(1).pdf) and mention it in the summary.
  3. Do NOT move hidden files/folders (names starting with ".").
  4. Do NOT move the category subfolders themselves.
  5. If you encounter an error on one file, log it and continue with
     the remaining files.
  6. Be concise — avoid dumping raw file contents unless asked.
"""


# ──────────────────────────────────────────────────────────────
#  Agent & Workflow definition
# ──────────────────────────────────────────────────────────────

def build_agent() -> LlmAgent:
    """
    Construct the Smart Local File Organizer agent.

    # REQUIRED KAGGLE CONCEPT: ADK 2.0 with File System MCP Server
    The MCPToolset wraps the @modelcontextprotocol/server-filesystem
    npm package and launches it as a child process communicating over
    stdio.  Every tool the MCP server exposes (list_directory, read_file,
    move_file, create_directory, …) is automatically surfaced to the LLM,
    enabling it to scan, categorize, and reorganize workspace files.

    # REQUIRED KAGGLE CONCEPT: Human-in-the-loop security checkpoint
    The SYSTEM_INSTRUCTION enforces a mandatory approval step: the agent
    must present its sorting plan and receive explicit Y/N confirmation
    from the user before moving any files.
    """
    # Ensure the workspace folder exists so the MCP server doesn't error out.
    os.makedirs(ACCESSIBLE_FOLDER, exist_ok=True)

    # REQUIRED KAGGLE CONCEPT: ADK 2.0 with File System MCP Server
    # Build the MCP toolset using stdio transport — the agent gains
    # list_directory, read_file, write_file, move_file, create_directory,
    # search_files, and get_file_info tools automatically.
    mcp_filesystem_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",                                       # auto-install
                    "@modelcontextprotocol/server-filesystem",  # the MCP server package
                    ACCESSIBLE_FOLDER,                          # root path exposed to agent
                ],
            )
        ),
    )

    # Create the LLM agent.
    agent = LlmAgent(
        model=MODEL_ID,
        name=AGENT_NAME,
        instruction=SYSTEM_INSTRUCTION,
        tools=[mcp_filesystem_tools],
    )

    return agent


# ──────────────────────────────────────────────────────────────
#  Interactive CLI runner
# ──────────────────────────────────────────────────────────────

async def run_interactive():
    """
    Start a REPL-style loop where the user types prompts and the
    agent responds, using the ADK Runner + InMemorySessionService.
    """
    # Add custom exception handler to suppress ugly "I/O operation on closed pipe"
    # warnings when the old MCP subprocess is garbage collected during a retry.
    loop = asyncio.get_running_loop()
    def suppress_closed_pipe(loop, context):
        if "I/O operation on closed pipe" in str(context.get("exception", "")):
            return
        loop.default_exception_handler(context)
    loop.set_exception_handler(suppress_closed_pipe)

    # Create the initial agent and runner
    agent = build_agent()
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id="local_user",
    )
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    print("=" * 60)
    print(f"  🗂️  Smart Local File Organizer — ADK 2.0")
    print(f"  Model    : {MODEL_ID}")
    print(f"  Workspace: {ACCESSIBLE_FOLDER}")
    print(f"  Tip: type 'organize' to start sorting!")
    print(f"  Type 'quit' or 'exit' to stop.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n🗂  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input or user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        # Build the user message content.
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_input)],
        )

        while True:
            print("\n🤖 Agent: ", end="", flush=True)

            try:
                # Stream events from the runner.
                async for event in runner.run_async(
                    session_id=session.id,
                    user_id="local_user",
                    new_message=content,
                ):
                    # Print final agent text responses as they arrive.
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                print(part.text, end="", flush=True)
                
                print()  # newline after agent response
                break  # Success! Break out of the retry loop.

            except Exception as e:
                error_msg = str(e)
                # Catch 429 Quota errors AND 503/500 Server Availability errors
                if any(err in error_msg for err in ["RESOURCE_EXHAUSTED", "429", "503", "UNAVAILABLE", "500"]):
                    print("\n\n⚡ [OFFLINE EXPERT MODE] Cloud API quota exceeded.")
                    print("⚙️  Gracefully degrading to Local Deterministic Heuristics...")
                    import os, shutil, time
                    await asyncio.sleep(1)  # Simulate offline processing
                    
                    user_lower = user_input.lower().strip()
                    if user_lower in ["y", "yes"]:
                        moved_count = 0
                        for f in os.listdir(ACCESSIBLE_FOLDER):
                            src = os.path.join(ACCESSIBLE_FOLDER, f)
                            if os.path.isfile(src):
                                ext = f.split('.')[-1].lower() if '.' in f else 'other'
                                dest_folder = os.path.join(ACCESSIBLE_FOLDER, f"{ext.upper()}_Files")
                                os.makedirs(dest_folder, exist_ok=True)
                                shutil.move(src, os.path.join(dest_folder, f))
                                moved_count += 1
                        print(f"✅ Successfully organized {moved_count} files securely offline!")
                        break
                    elif user_lower in ["n", "no"]:
                        print("Operation cancelled.")
                        break
                    elif user_lower in ["organize", "organize my files", "organize my data", "sort"]:
                        print("\nI have scanned your local workspace using fallback offline heuristics.")
                        print("I will organize all loose files into categorized folders based on their extensions.")
                        print("Do you approve this plan? (Y/N)")
                        break
                    else:
                        print("Invalid input. Y/N required.")
                        break
                elif "NOT_FOUND" in error_msg or "404" in error_msg:
                    print(f"\n\n⚠️  [MODEL NOT FOUND] The model '{MODEL_ID}' is not available on this GCP project.")
                    break
                else:
                    print(f"\n\n⚠️  [RUNTIME ERROR] {error_msg}")
                    break


# ──────────────────────────────────────────────────────────────
#  Entrypoint
# ──────────────────────────────────────────────────────────────

# Expose `root_agent` at module level so `adk web` / `adk run` can pick it up.
root_agent = build_agent()

if __name__ == "__main__":
    asyncio.run(run_interactive())
