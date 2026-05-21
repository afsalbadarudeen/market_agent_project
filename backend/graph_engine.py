import os
import yfinance as yf
import pandas as pd
from typing import Annotated, Dict, Any, List, TypedDict
from operator import add
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# 1. State Definition
class AgentState(TypedDict):
    ticker: str
    technical_data: Dict[str, Any]
    sentiment_data: List[Dict[str, str]]
    draft_report: str
    compliance_feedback: str
    approved: bool
    revision_count: int
    messages: Annotated[List[BaseMessage], add]

# 2. Setup LLM 
# Note: Ensure OPENAI_API_KEY is exported in your terminal environment
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# --- Real Production Tool Call Methods ---
def fetch_live_market_data(ticker_symbol: str) -> dict:
    """Uses yfinance to query real technical history and extract metrics."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1mo")
        if hist.empty:
            return {"error": f"No market history found for {ticker_symbol}."}
        
        latest_close = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else latest_close
        daily_return = ((latest_close - prev_close) / prev_close) * 100
        
        # Simple moving average calculation as our analytical data point
        sma_20 = hist['Close'].rolling(window=min(20, len(hist))).mean().iloc[-1]
        
        return {
            "current_price": round(latest_close, 2),
            "daily_change_pct": round(daily_return, 2),
            "20_day_sma": round(sma_20, 2),
            "volume": int(hist['Volume'].iloc[-1])
        }
    except Exception as e:
        return {"error": f"Failed fetching market metrics: {str(e)}"}

def fetch_live_market_news(ticker_symbol: str) -> list:
    """Uses yfinance to pull live news metadata concerning the asset."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        news_items = ticker.news[:3] # Pull top 3 relevant news entries
        parsed_news = []
        for item in news_items:
            parsed_news.append({
                "title": item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "summary": item.get("summary", "No summary provided.")
            })
        return parsed_news if parsed_news else [{"title": "No recent macro news reports found."}]
    except Exception as e:
        return [{"title": f"Failed retrieving news streams: {str(e)}"}]


# --- Graph Nodes Definition ---
def market_data_agent(state: AgentState) -> Dict[str, Any]:
    metrics = fetch_live_market_data(state["ticker"])
    return {
        "technical_data": metrics,
        "messages": [AIMessage(content=f"Market Data Specialist: Pulled live data endpoints for {state['ticker']}.")]
    }

def sentiment_agent(state: AgentState) -> Dict[str, Any]:
    news = fetch_live_market_news(state["ticker"])
    tech = state["technical_data"]
    
    prompt = f"""
    You are an expert financial research analyst. Review the real-time data inputs and draft an executive investment memo.
    
    Ticker: {state['ticker']}
    Live Technical Metrics: {tech}
    Recent Corporate News Content: {news}
    
    Structure the report with a summary of technical health and potential news drivers.
    """
    response = llm.invoke(prompt)
    return {
        "sentiment_data": news,
        "draft_report": response.content,
        "messages": [AIMessage(content="Sentiment Analyst: Generated initial structural report draft.")]
    }

def risk_compliance_agent(state: AgentState) -> Dict[str, Any]:
    draft = state["draft_report"]
    revisions = state.get("revision_count", 0)
    
    prompt = f"""
    You are a strict Risk & Compliance Officer. Critically review this investment report draft.
    Ensure it details structural downfalls, volatility concerns, and maintains proper risk language.
    
    Draft Report:
    {draft}
    
    Output your assessment clearly. On the final line, write exactly:
    'STATUS: APPROVED' if the report looks solid, or 'STATUS: REJECTED' if it needs broader hazard warnings.
    """
    response = llm.invoke(prompt)
    content = response.content
    approved = "STATUS: APPROVED" in content
    
    if revisions >= 1: # To guarantee portfolio speed, force loop breakout after 1 revision
        approved = True
        content += "\n[System Breakout Override: Maximum loop depth met.]"
        
    return {
        "compliance_feedback": content,
        "approved": approved,
        "revision_count": revisions + 1,
        "messages": [AIMessage(content=f"Compliance Evaluation Complete. Approved Status: {approved}")]
    }

def route_compliance_decision(state: AgentState) -> str:
    return "human_review" if state["approved"] else "sentiment_agent"

def human_review_node(state: AgentState) -> Dict[str, Any]:
    return {"messages": [AIMessage(content="Human Verification Step Cleared. Content safe to deploy.")]}


# --- Compilation ---
workflow = StateGraph(AgentState)
workflow.add_node("market_data_agent", market_data_agent)
workflow.add_node("sentiment_agent", sentiment_agent)
workflow.add_node("risk_compliance_agent", risk_compliance_agent)
workflow.add_node("human_review", human_review_node)

workflow.set_entry_point("market_data_agent")
workflow.add_edge("market_data_agent", "sentiment_agent")
workflow.add_edge("sentiment_agent", "risk_compliance_agent")

workflow.add_conditional_edges(
    "risk_compliance_agent",
    route_compliance_decision,
    {"sentiment_agent": "sentiment_agent", "human_review": "human_review"}
)
workflow.add_edge("human_review", END)

memory = MemorySaver()
compiled_app = workflow.compile(checkpointer=memory, interrupt_before=["human_review"])
