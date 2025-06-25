"""Entry point for the EU AI Act Compliance Checker application."""

import os
import sys
import streamlit as st
from app.ui.main import main as run_app
from app.utils.initialization import initialize_app

if __name__ == "__main__":
    # Add the current directory to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize the application (download EU AI Act and create vector store)
    initialization_result = initialize_app()
    if initialization_result["status"] != "success":
        print(f"Warning: Application initialization had issues: {initialization_result['error']}")
    else:
        print(f"Application initialized successfully. Vector store has {initialization_result['vectorstore_size']} documents.")
    
    # Run the Streamlit app
    run_app()