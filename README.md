<div align="center">
  <h1>🗂️ Kaggle Concierge Agent</h1>
  <p>A focused, local automation script for file-system orchestration and Kaggle workflows.</p>
</div>

---

## 📖 Overview

**Kaggle Concierge Agent** is a streamlined Python automation utility designed to orchestrate your local file-system and interface seamlessly with Kaggle. Rather than over-engineering a bloated microservice architecture, this repository keeps its logic contained within a single, highly effective script (`agent.py`).

## 🏗️ Script Architecture

The entire workflow is driven by `agent.py`, which acts as the singular entry point for:
- **File-System Orchestration:** Organizes, moves, and manages files within your local `workspace/` directory autonomously.
- **Human-in-the-Loop Interruption:** Contains robust exception handling and fallback logic that safely pauses execution when manual user confirmation or intervention is required.
- **Kaggle API Interfacing:** Connects to datasets and competitions natively.

*Design Philosophy:* This is not a distributed microservice deployment; it is a specialized local developer tool. Keeping the entire orchestration logic within a single Python script allows for rapid iteration, simple execution, and immediate debuggability without complex containerization.

## 🚀 Getting Started

1. **Environment Setup:** Ensure you have your `KAGGLE_USERNAME` and `KAGGLE_KEY` set in your environment variables or local `~/.kaggle/kaggle.json`.
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Orchestrator:**
   ```bash
   python agent.py
   ```

## 📜 License
Distributed under the MIT License.
