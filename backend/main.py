import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend.graph_engine import compiled_app, HumanMessage

app = FastAPI(title="Autonomous Market Analyst Back-End Server")

class AnalysisRequest(BaseModel):
    ticker: str
    thread_id: str

class ApproveRequest(BaseModel):
    thread_id: str

@app.post("/api/analyze")
async def start_analysis(payload: AnalysisRequest):
    """Initializes the multi-agent graph run."""
    config = {"configurable": {"thread_id": payload.thread_id}}
    initial_state = {
        "ticker": payload.ticker.upper(),
        "revision_count": 0,
        "approved": False,
        "messages": [HumanMessage(content=f"Initiating analysis sequence for {payload.ticker}")]
    }
    
    # Run graph tracking until it encounters our defined breakpoint node
    try:
        compiled_app.invoke(initial_state, config)
        return get_current_graph_state(payload.thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{thread_id}")
def get_status(thread_id: str):
    """Fetches current workflow positioning and state data dumps."""
    return get_current_graph_state(thread_id)

@app.post("/api/approve")
async def approve_report(payload: ApproveRequest):
    """Acts as the manual human-in-the-loop breakout mechanism to finish execution."""
    config = {"configurable": {"thread_id": payload.thread_id}}
    try:
        # Passing None signals the thread memory to step forward from its saved position
        compiled_app.invoke(None, config)
        return get_current_graph_state(payload.thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_current_graph_state(thread_id: str) -> Dict[str, Any]:
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = compiled_app.get_state(config)
    
    # Check if the next pointer points to our human node block
    is_paused = len(state_snapshot.next) > 0 and "human_review" in state_snapshot.next[0]
    values = state_snapshot.values
    
    return {
        "thread_id": thread_id,
        "current_position": list(state_snapshot.next),
        "status": "PAUSED_AWAITING_HUMAN" if is_paused else "COMPLETED",
        "ticker": values.get("ticker", ""),
        "technical_data": values.get("technical_data", {}),
        "draft_report": values.get("draft_report", ""),
        "compliance_feedback": values.get("compliance_feedback", "")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
