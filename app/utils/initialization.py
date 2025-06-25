"""Initialization module for the application."""

import os
import sys
from typing import Dict, Any
from app.utils.config import get_data_dir
from app.utils.download_ai_act import download_eu_ai_act
from app.tools.eu_ai_act_handler import EUAIActHandler

def initialize_app():
    """Initialize the application by creating necessary directories and downloading files.
    
    Returns:
        Dict with initialization status information.
    """
    try:
        # Create data directories
        data_dir = get_data_dir()
        repos_dir = os.path.join(data_dir, "repos")
        vectorstores_dir = os.path.join(data_dir, "vectorstores")
        
        os.makedirs(repos_dir, exist_ok=True)
        os.makedirs(vectorstores_dir, exist_ok=True)
        
        print(f"Created data directories at {data_dir}")
        
        # Download EU AI Act if not already downloaded
        ai_act_path = os.path.join(data_dir, "eu_ai_act.txt")
        if not os.path.exists(ai_act_path):
            download_eu_ai_act(ai_act_path)
            print(f"Downloaded EU AI Act to {ai_act_path}")
        
        # Process EU AI Act and create vector store
        ai_act_handler = EUAIActHandler()
        vectorstore = ai_act_handler.process_ai_act()
        print("Processed EU AI Act and created vector store")
        
        return {
            "status": "success",
            "data_dir": data_dir,
            "ai_act_path": ai_act_path,
            "vectorstore_size": len(vectorstore.index_to_docstore_id)
        }
        
    except Exception as e:
        print(f"Error initializing application: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    result = initialize_app()
    print(f"Initialization result: {result}")
