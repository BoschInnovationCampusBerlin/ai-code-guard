"""Helper functions for the Streamlit UI."""

import streamlit as st
import json
from typing import Dict, Any, List, Optional
import time

def display_header():
    """Display the application header."""
    st.title("EU AI Act Compliance Checker")
    st.markdown(
        """
        This application analyzes GitHub repositories and checks their compliance with the EU AI Act.
        
        ✅ Clone and analyze GitHub repositories  
        ✅ Extract technical features and capabilities from code  
        ✅ Identify relevant sections of the EU AI Act  
        ✅ Generate compliance reports with recommendations
        """
    )

def display_repository_form():
    """Display the repository form.
    
    Returns:
        Tuple of (repo_url, branch) if form is submitted, None otherwise.
    """
    with st.form("repo_form"):
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/username/repository"
        )
        
        branch = st.text_input(
            "Branch",
            value="main",
            placeholder="main"
        )
        
        st.info("Note: This application works with public GitHub repositories without requiring authentication.")
        
        submitted = st.form_submit_button("Analyze Repository")
        
        if submitted and repo_url:
            return repo_url, branch
        
        return None

def display_loading_spinner(step: str):
    """Display a loading spinner for the current step.
    
    Args:
        step: Current step name.
    """
    if step == "download_repo":
        message = "Downloading and extracting repository..."
    elif step == "analyze_repo":
        message = "Analyzing repository code..."
    elif step == "analyze_compliance":
        message = "Checking compliance with EU AI Act..."
    else:
        message = "Processing..."
        
    with st.spinner(message):
        # Just to show the spinner, as the actual work is done elsewhere
        time.sleep(0.1)

def display_repository_analysis(repo_analysis: Dict[str, Any]):
    """Display repository analysis results.
    
    Args:
        repo_analysis: Repository analysis results.
    """
    st.header("Repository Analysis")
    
    # Display repository summary
    st.subheader("Technical Summary")
    st.markdown(repo_analysis.get("repository_summary", "No summary available"))
    
    # Display file analyses
    with st.expander("File Analyses Details"):
        file_analyses = repo_analysis.get("file_analyses", [])
        
        if not file_analyses:
            st.info("No file analyses available")
        else:
            for file_analysis in file_analyses:
                file_path = file_analysis.get("file_path", "Unknown file")
                analysis = file_analysis.get("analysis", {})
                
                st.markdown(f"**File:** `{file_path}`")
                
                if analysis:
                    if "technical_summary" in analysis:
                        st.markdown("**Technical Summary:**")
                        st.markdown(analysis.get("technical_summary", "No summary available"))
                        
                    if "ai_capabilities" in analysis:
                        ai_capabilities = analysis.get("ai_capabilities", [])
                        if ai_capabilities:
                            st.markdown("**AI Capabilities:**")
                            for capability in ai_capabilities:
                                st.markdown(f"- {capability}")
                                
                    if "regulatory_concerns" in analysis:
                        st.markdown("**Regulatory Concerns:**")
                        st.markdown(analysis.get("regulatory_concerns", "None identified"))
                else:
                    st.info("No analysis available for this file")
                    
                st.markdown("---")

def display_compliance_analysis(compliance_analysis: Dict[str, Any]):
    """Display compliance analysis results.
    
    Args:
        compliance_analysis: Compliance analysis results.
    """
    st.header("EU AI Act Compliance Analysis")
    
    # Display the compliance analysis
    st.markdown(compliance_analysis.get("compliance_analysis", "No compliance analysis available"))
    
    # Display relevant sections
    with st.expander("Relevant EU AI Act Sections"):
        relevant_sections = compliance_analysis.get("relevant_sections", [])
        
        if not relevant_sections:
            st.info("No relevant sections found")
        else:
            for i, section in enumerate(relevant_sections, 1):
                st.markdown(f"### Section {i}")
                st.markdown(section)
                st.markdown("---")

def display_error(error: str):
    """Display an error message.
    
    Args:
        error: Error message.
    """
    st.error(f"Error: {error}")

def display_status(status: str):
    """Display the current status.
    
    Args:
        status: Current status.
    """
    if status == "completed":
        st.success("Analysis completed successfully!")
    elif status == "error":
        st.warning("Analysis completed with errors")
    else:
        st.info(f"Status: {status}")

def custom_json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default json code.
    
    Args:
        obj: The object to serialize.
        
    Returns:
        A serializable version of the object.
    """
    # Handle langchain message objects
    if hasattr(obj, "content") and hasattr(obj, "type"):
        return {
            "content": obj.content,
            "type": obj.type
        }
    
    # Handle langchain message-like objects without explicit type
    if hasattr(obj, "content") and hasattr(obj, "__class__"):
        return {
            "content": obj.content,
            "type": obj.__class__.__name__
        }
    
    # Handle objects with custom string representation
    try:
        return str(obj)
    except:
        return "Non-serializable object"

def process_dict_for_json(data_dict: Dict) -> Dict:
    """Process a dictionary to make it JSON serializable.
    
    Args:
        data_dict: Dictionary to process.
        
    Returns:
        A JSON serializable dictionary.
    """
    result = {}
    for key, value in data_dict.items():
        if isinstance(value, dict):
            result[key] = process_dict_for_json(value)
        elif isinstance(value, list):
            result[key] = process_list_for_json(value)
        else:
            try:
                # Test if the value is JSON serializable
                json.dumps(value)
                result[key] = value
            except TypeError:
                result[key] = custom_json_serializer(value)
    return result

def process_list_for_json(data_list: List) -> List:
    """Process a list to make it JSON serializable.
    
    Args:
        data_list: List to process.
        
    Returns:
        A JSON serializable list.
    """
    result = []
    for item in data_list:
        if isinstance(item, dict):
            result.append(process_dict_for_json(item))
        elif isinstance(item, list):
            result.append(process_list_for_json(item))
        else:
            try:
                # Test if the value is JSON serializable
                json.dumps(item)
                result.append(item)
            except TypeError:
                result.append(custom_json_serializer(item))
    return result

def display_download_button(data: Dict[str, Any], filename: str = "compliance_analysis.json"):
    """Display a button to download the analysis results.
    
    Args:
        data: Data to download.
        filename: Name of the download file.
    """
    if data:
        # Create a copy of the data to process
        processed_data = {}
        try:
            # Deep copy and process the data to make it JSON serializable
            for key, value in data.items():
                if isinstance(value, dict):
                    processed_data[key] = process_dict_for_json(value)
                elif isinstance(value, list):
                    processed_data[key] = process_list_for_json(value)
                else:
                    try:
                        # Test if the value is JSON serializable
                        json.dumps(value)
                        processed_data[key] = value
                    except TypeError:
                        processed_data[key] = custom_json_serializer(value)
                        
            json_data = json.dumps(processed_data, indent=2, default=custom_json_serializer)
            st.download_button(
                label="Download Analysis Report",
                data=json_data,
                file_name=filename,
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Error preparing download: {str(e)}")
            st.info("You can still view the analysis results on this page.")
