"""Main Streamlit application."""

import streamlit as st
import os
import sys
from typing import Dict, Any, List, Optional
import json
import time

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agents.compliance_agent import ComplianceChecker
from app.ui.ui_helpers import (
    display_header,
    display_repository_form,
    display_loading_spinner,
    display_repository_analysis,
    display_compliance_analysis,
    display_error,
    display_status,
    display_download_button
)

# Set page configuration
st.set_page_config(
    page_title="EU AI Act Compliance Checker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize the session state variables."""
    if "compliance_checker" not in st.session_state:
        st.session_state.compliance_checker = ComplianceChecker()
        
    if "result" not in st.session_state:
        st.session_state.result = None
        
    if "step" not in st.session_state:
        st.session_state.step = None
        
    if "status" not in st.session_state:
        st.session_state.status = None
        
    if "error" not in st.session_state:
        st.session_state.error = None

def update_session_state(result):
    """Update the session state with the latest result.
    
    Args:
        result: The latest result from the compliance checker.
    """
    st.session_state.result = result
    st.session_state.step = result.get("current_step")
    st.session_state.status = result.get("status")
    st.session_state.error = result.get("error")

def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Sidebar information
    with st.sidebar:
        st.header("About")
        st.markdown(
            """
            This tool helps you assess if your AI project complies with the 
            EU AI Act by analyzing your GitHub repository and identifying relevant 
            regulatory requirements.
            
            The EU AI Act is a comprehensive regulatory framework that aims to ensure 
            AI systems deployed in the EU are safe, transparent, traceable, non-discriminatory, 
            and environmentally friendly.
            """
        )
        
        st.info("💡 This tool works with any public GitHub repository without requiring authentication.")
        
        # Show EU AI Act info
        try:
            from app.utils.config import get_data_dir
            import os
            ai_act_path = os.path.join(get_data_dir(), "eu_ai_act.txt")
            vector_store_path = os.path.join(get_data_dir(), "vectorstores", "eu_ai_act")
            
            if os.path.exists(ai_act_path):
                file_size = round(os.path.getsize(ai_act_path) / 1024, 2)  # Size in KB
                st.success(f"✅ EU AI Act loaded ({file_size} KB)")
            else:
                st.warning("⚠️ EU AI Act not found")
        except Exception:
            pass
        
        st.header("How It Works")
        st.markdown(
            """
            1. Enter your GitHub repository URL
            2. Our AI agent analyzes your code
            3. The system identifies AI capabilities
            4. Relevant sections of the EU AI Act are matched
            5. A compliance report is generated
            """
        )
    
    # Display repository form
    form_result = display_repository_form()
    
    if form_result:
        repo_url, branch = form_result
        
        # Reset session state
        st.session_state.result = None
        st.session_state.step = "download_repo"
        st.session_state.status = "starting"
        st.session_state.error = None
        
        # Run compliance check
        with st.spinner("Analyzing repository..."):
            result = st.session_state.compliance_checker.check_repository(repo_url, branch)
            update_session_state(result)
    
    # Display results if available
    if st.session_state.result:
        result = st.session_state.result
        
        if st.session_state.error:
            display_error(st.session_state.error)
        else:
            display_status(st.session_state.status)
            
            # Display results tabs
            if "repo_analysis" in result and result["repo_analysis"]:
                tab1, tab2 = st.tabs(["Repository Analysis", "Compliance Analysis"])
                
                with tab1:
                    display_repository_analysis(result["repo_analysis"])
                    
                with tab2:
                    if "compliance_analysis" in result and result["compliance_analysis"]:
                        display_compliance_analysis(result["compliance_analysis"])
                    else:
                        st.info("Compliance analysis not available yet")
                
                # Display download button
                display_download_button(result, "eu_ai_act_compliance_report.json")

if __name__ == "__main__":
    main()
