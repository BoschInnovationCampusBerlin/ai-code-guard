"""Test for the vector store functionality."""

import sys
import os
import unittest

# Add the parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.eu_ai_act_handler import EUAIActHandler

class TestVectorStore(unittest.TestCase):
    """Test case for vector store functionality."""
    
    def test_process_ai_act(self):
        """Test processing the EU AI Act and creating/loading vector store."""
        handler = EUAIActHandler()
        
        # First call should create the vector store if it doesn't exist
        vectorstore = handler.process_ai_act()
        self.assertIsNotNone(vectorstore)
        
        # Second call should load the existing vector store
        vectorstore2 = handler.process_ai_act()
        self.assertIsNotNone(vectorstore2)
        
        # Test search functionality
        results = handler.search_relevant_sections("data protection", k=2)
        self.assertIsNotNone(results)
        self.assertLessEqual(len(results), 2)  # Should return at most 2 results

if __name__ == "__main__":
    unittest.main()
