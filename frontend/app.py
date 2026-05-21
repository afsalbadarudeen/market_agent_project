import streamlit as st
import requests
import uuid

BACKEND_URL = "http://localhost:8000/api"

st.set_page_config(page_title="AI Financial Intelligence Agent", page_icon="📈", layout="wide")
st.title("📈 Autonomous Multi-Agent Market Analyst")
st.caption("Powered by LangGraph, FastAPI, and Real-Time Yahoo Finance API Engine Tasks")

# Maintain explicit thread continuity state within client dashboard
if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"dashboard_session_{uuid.uuid4().hex[:6]}"
if "graph_data" not in st.session_state:
    st.session_state.graph_data = None

# Sidebar controls
st.sidebar.header("Agent Configuration Target")
ticker_input = st.sidebar.text_input("Stock Ticker Target (e.g., AAPL, NVDA, MSFT)", value="NVDA")
run_btn = st.sidebar.button("Launch Analysis Stream", use_container_width=True)

if run_btn:
    with st.spinner(f"Orchestrating agent subroutines for {ticker_input}... Calling live APIs..."):
        payload = {"ticker": ticker_input, "thread_id": st.session_state.thread_id}
        res = requests.post(f"{BACKEND_URL}/analyze", json=payload)
        if res.status_code == 200:
            st.session_state.graph_data = res.json()
            st.toast("Agent nodes processing completed successfully!", icon="✅")
        else:
            st.error(f"Backend processing failure: {res.text}")

# Main Interface Layout based on Graph Execution Outputs
data = st.session_state.graph_data

if data:
    st.subheader(f"Current Dashboard Context: State Stream Data for `{data['ticker']}`")
    
    # 1. State Information Dashboard Boxes
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ticker Value Target", data["ticker"])
    with col2:
        st.metric("Live Market Spot Price", f"${data['technical_data'].get('current_price', 'N/A')}")
    with col3:
        st.metric("Daily Market Volatility Delta", f"{data['technical_data'].get('daily_change_pct', 'N/A')}%")
    with col4:
        status_color = "🔴 PAUSED" if data["status"] == "PAUSED_AWAITING_HUMAN" else "🟢 SUCCESS"
        st.metric("Graph Execution Phase", status_color)
        
    st.markdown("---")
    
    # 2. Side-by-Side Agent Result Panel Display
    left_panel, right_panel = st.columns(2)
    
    with left_panel:
        st.markdown("### 📝 Sentiment Specialist: Analyst Research Draft")
        st.info(data["draft_report"] if data["draft_report"] else "No draft constructed yet.")
        
    with right_panel:
        st.markdown("### 🛡️ Compliance Officer: Internal Evaluation Critique")
        st.warning(data["compliance_feedback"] if data["compliance_feedback"] else "No compliance review logs stored.")
        
    st.markdown("---")
    
    # 3. Dynamic Human-In-The-Loop Execution Breakout Trigger Section
    if data["status"] == "PAUSED_AWAITING_HUMAN":
        st.error("⚠️ HUMAN REVIEW MANDATED: The workflow state has paused at the `human_review` node checkpoint.")
        st.write("Please inspect the analyst's research memo and the compliance officer's critique above. If satisfied, release the report below.")
        
        if st.button("Confirm Compliance Clear & Release Final Report", type="primary", use_container_width=True):
            with st.spinner("Injecting human confirmation callback signal into active state machine..."):
                approve_payload = {"thread_id": data["thread_id"]}
                res = requests.post(f"{BACKEND_URL}/approve", json=approve_payload)
                if res.status_code == 200:
                    st.session_state.graph_data = res.json()
                    st.success("Report approved! Workflow has safely exited and run is complete.")
                    st.rerun()
                else:
                    st.error(f"Error resuming graph execution: {res.text}")
    else:
        st.success("🎉 PIPELINE RUN COMPLETE: Final investment report cleared and saved to state checkpointer storage successfully.")
else:
    st.info("Input a target stock ticker in the sidebar and trigger the analysis run to see the autonomous multi-agent system cycle in real-time.")
