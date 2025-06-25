"""Initialization module for the application."""

import os
import sys
from typing import Dict, Any
from langchain_community.vectorstores import FAISS
from app.utils.config import get_data_dir, get_embeddings
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
        
        # Check if vector store already exists to avoid unnecessary processing
        vectorstore_path = os.path.join(data_dir, "vectorstores", "eu_ai_act")
        if os.path.exists(vectorstore_path):
            try:
                embeddings = get_embeddings()
                vectorstore = FAISS.load_local(
                    vectorstore_path, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                print("Loaded existing vector store")
                
                return {
                    "status": "success",
                    "data_dir": data_dir,
                    "ai_act_path": ai_act_path,
                    "vectorstore_size": len(vectorstore.index_to_docstore_id)
                }
            except Exception as load_error:
                print(f"Error loading existing vector store: {load_error}")
                # Continue to processing
        
        # Process the EU AI Act in batches
        try:
            vectorstore = ai_act_handler.process_ai_act()
            print("Processed EU AI Act and created vector store")
            
            return {
                "status": "success",
                "data_dir": data_dir,
                "ai_act_path": ai_act_path,
                "vectorstore_size": len(vectorstore.index_to_docstore_id)
            }
        except Exception as process_error:
            print(f"Error processing EU AI Act: {process_error}")
            # Return a partial success if we have at least the data files
            return {
                "status": "partial",
                "error": str(process_error),
                "data_dir": data_dir,
                "ai_act_path": ai_act_path,
                "message": "Application can run with limited functionality"
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
