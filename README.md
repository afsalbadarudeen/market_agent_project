# Autonomous Market Analyst Agent (LangGraph & FastAPI)

An enterprise-grade, stateful multi-agent system built from scratch using **LangGraph**, **FastAPI**, and **Streamlit**. This project demonstrates an autonomous financial research pipeline that handles real-time quantitative data retrieval, asynchronous cyclic text refinement (Critique-and-Refine loops), state persistence, and manual human-in-the-loop validation barriers.

Unlike simple linear LLM chains, this application treats research as an event-driven state machine, ensuring structured coordination, guardrails, and compliance oversight before data presentation.

---

## 🚀 System Architecture & Core Workflow

The architecture is built as a stateful, cyclic directed graph using `LangGraph`. The global graph memory object (`AgentState`) is mutated sequentially by specialist node agents and evaluated by conditional routers.

```text
                  +-----------------------+
                  |  User Input (Ticker)  |
                  +-----------+-----------+
                              |
                              v
                   +---------------------+
                   |  Market Data Agent  | <--- (Fetches Live yFinance Technicals)
                   +----------+----------+
                              |
                              v
                   +---------------------+
                   |   Sentiment Agent   | <--- (Combines Data + Pulls Top News)
                   +----------+----------+
                              |
                              v
                +-------------v-------------+
                |   Risk Compliance Agent   | <---------+
                +-------------+-------------+           |
                              |                         |
                              v                         | (If REJECTED:
                    /// Router Decision \\\             |  Loops back with feedback)
                   /                       \            |
                  <  Approved?  or  Reject? > ----------+
                   \                       /
                    \\\       Total       ///
                              |
                              | (If APPROVED: Interrupt state triggered)
                              v
                +-------------+-------------+
                |    Human Review Node      | 🛑 [STATE CHECKPOINT INTERRUPT]
                |   (Awaiting API Signal)   |
                +-------------+-------------+
                              |
                              v
                   +---------------------+
                   |    Final Report     |
                   +---------------------+
```
##  🛠️ Key Technical Highlights & Production Design
Stateful Multi-Agent Orchestration: Uses LangGraph to maintain an explicit thread-safe state schema. Agents act as isolated computing blocks mutating specific portions of the global memory canvas.

Asynchronous Critique & Refine Loop: Features a logical routing boundary where a dedicated Risk and Compliance Agent checks the generated report against structural vulnerabilities. If flagged, it loops backwards to the Sentiment Agent with an ruggedized revision counter to protect against infinite runtime loops.

State Persistence & Resilience: Configured with an explicit compilation step using MemorySaver. Every state transition is automatically saved to a persistent thread checkpointer database, allowing complete crash recovery and long-running execution continuity.

Human-In-The-Loop Execution Barrier: Implements interrupt_before=["human_review"]. When an investment draft is cleared by automated risk checks, the entire backend graph engine completely freezes. It exposes state metrics via REST API endpoints and awaits an authorized manual human webhook trigger to safely exit the thread.

Production Tool Integrations: Powered by live quantitative tool abstractions wrapped inside yfinance to parse active pricing, moving averages, and market news streams dynamically based on user choices.

## 📦 Project Directory Structure

```text
market_agent_project/
│
├── backend/
│   ├── main.py          # FastAPI server
│   └── graph_engine.py  # LangGraph logic
│
├── frontend/
│   └── app.py           # Streamlit UI
│
├── requirements.txt
└── README.md
```

## 🔄 Workflow Explanation
1. Data Collection

Fetches live market data (price, volume, trends).

2. Sentiment Analysis

Combines technical data with news insights.

3. Compliance Check

Validates output against risk constraints.

4. Human Approval

Execution pauses for manual validation.

5. Final Report

Generates structured financial analysis.
