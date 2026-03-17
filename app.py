import streamlit as st
import json
import asyncio
import os
from typing import Dict, List, Any
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.model_client import ModelClient
from evaluation.response_evaluator import ResponseEvaluator
from evaluation.scoring_engine import ScoringEngine
from analysis.report_generator import ReportGenerator
from visualization.dashboard import DashboardVisualizer
from utils.config import get_config
from utils.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()

# ---- Layout Configuration ----
st.set_page_config(
    page_title="LLM Safety Evaluator",
    page_icon="🛡️",
    layout="wide"
)

# ---- Utility Functions ----
@st.cache_data
def load_prompts() -> Dict[str, List[str]]:
    """Load the adversarial dataset."""
    try:
        path = os.path.join(os.path.dirname(__file__), "datasets", "safety_prompts.json")
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        st.error("Failed to load safety prompts. Check datasets/safety_prompts.json.")
        return {}

def flatten_prompts(dataset: Dict[str, List[str]], limit_per_category: int) -> List[Dict[str, str]]:
    """Convert JSON block into a flat list of dicts with category labels."""
    flat_list = []
    for category, prompts in dataset.items():
        for p in prompts[:limit_per_category]:
             flat_list.append({"category": category, "prompt": p})
    return flat_list

async def run_evaluation(client: ModelClient, prompts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Run prompts through the model client asynchronously and evaluate them."""
    results = []
    
    # Setup Streamlit progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(prompts)
    
    # We could batch this using client.generate_batch_responses, but doing it sequentially 
    # here allows real-time UI updates in Streamlit
    for i, item in enumerate(prompts):
        prompt_text = item["prompt"]
        category = item["category"]
        
        status_text.text(f"Testing [{category}]: {prompt_text[:50]}...")
        
        # 1. Generate Response
        api_result = await client.generate_response(prompt_text)
        
        # 2. Evaluate Response
        response_text = api_result.get("response", "")
        classification = ResponseEvaluator.evaluate(category, prompt_text, response_text)
        
        # 3. Store Data
        results.append({
             "category": category,
             "prompt": prompt_text,
             "response": response_text,
             "latency_seconds": api_result.get("latency_seconds", 0),
             "classification": classification
        })
        
        progress_bar.progress((i + 1) / total)
        
    status_text.text("Evaluation Complete.")
    return results

# ---- Main Streamlit UI ----
def main():
    dataset = load_prompts()

    # Sidebar: Model Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        format_type = st.selectbox("API Format", ["openai", "gemini", "custom"])
        
        # Adjust default endpoint based on selected format
        default_endpoint = "https://api.openai.com/v1/chat/completions"
        default_model = "gpt-3.5-turbo"
        if format_type == "gemini":
             default_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
             default_model = "gemini-1.5-flash"
             
        endpoint = st.text_input("API Endpoint", value=default_endpoint)
        api_key = st.text_input("API Key", type="password")
        model_name = st.text_input("Model Name", value=default_model)
        
        st.divider()
        st.subheader("Evaluation Settings")
        limit = st.slider("Prompts per category", min_value=1, max_value=20, value=5)
        
        # Pre-calculate totals
        total_prompts = sum([len(p[:limit]) for p in dataset.values()])
        st.caption(f"Total planned tests: {total_prompts}")
        
        run_btn = st.button("Run Safety Evaluation", type="primary", use_container_width=True)

    # Main Area
    DashboardVisualizer.render_header(model_name)

    if not run_btn:
        st.info("👈 Please configure the model endpoint and click 'Run Safety Evaluation' to begin.")
        
        # Display sample prompts as a placeholder
        with st.expander("View Dataset Sample"):
            st.json({k: v[:2] for k,v in dataset.items()})
        return

    # User clicked RUN
    if not api_key:
        st.error("API Key is required to run evaluations.")
        return
        
    flat_prompts = flatten_prompts(dataset, limit)
    client = ModelClient(endpoint, api_key, model_name, format_type)
    
    with st.spinner("Initializing evaluation engine..."):
        # Run async loop in synchronous Streamlit script
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
             results = loop.run_until_complete(run_evaluation(client, flat_prompts))
        finally:
             loop.close()
             
    if not results:
        st.error("Evaluation completed but yielded no results.")
        return
        
    # Analyze data
    summary = ScoringEngine.generate_score_summary(results)
    recommendations_list = ReportGenerator.generate_recommendations(summary["category_scores"])
    
    # Render Dashboard Tabs
    tabs = st.tabs(["📊 Dashboard Overview", "🛡️ Vulnerability Report", "🔍 Deep Inspection"])
    
    with tabs[0]:
        DashboardVisualizer.render_overview_metrics(summary)
        col1, col2 = st.columns(2)
        with col1:
            DashboardVisualizer.render_category_chart(summary["category_scores"])
        with col2:
            DashboardVisualizer.render_distribution_chart(summary["distribution"])
            
    with tabs[1]:
        # Merge recommendation text with scores
        enriched_recs = []
        for cat, score in summary["category_scores"].items():
             # Find matched rule
             for r in recommendations_list:
                  if r["category"] == cat:
                      enriched_recs.append(r)
                      break
        # Adding explicitly clear categories too if missing from report
        for r in recommendations_list:
              if r["category"] == "All Clear":
                  enriched_recs.append(r)
                  
        DashboardVisualizer.render_recommendations(enriched_recs)
             
    with tabs[2]:
        DashboardVisualizer.render_inspection_table(results)

if __name__ == "__main__":
    main()
