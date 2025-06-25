"""Test for JSON serialization of LangChain objects."""

import json
import sys
import os
import unittest

# Add the parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.ui_helpers import (
    custom_json_serializer,
    process_dict_for_json,
    process_list_for_json
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class TestJSONSerialization(unittest.TestCase):
    """Test case for JSON serialization."""
    
    def test_message_serialization(self):
        """Test serialization of LangChain message objects."""
        # Create test messages
        system_message = SystemMessage(content="This is a system message")
        human_message = HumanMessage(content="This is a human message")
        ai_message = AIMessage(content="This is an AI message")
        
        # Test direct serialization of message objects
        system_dict = custom_json_serializer(system_message)
        self.assertEqual(system_dict["content"], "This is a system message")
        self.assertTrue("type" in system_dict)
        
        # Test nested dictionary serialization
        test_dict = {
            "messages": [system_message, human_message, ai_message],
            "metadata": {
                "timestamp": "2023-01-01",
                "nested_message": system_message
            }
        }
        
        serialized_dict = process_dict_for_json(test_dict)
        
        # Verify the serialized dictionary
        self.assertIsInstance(serialized_dict, dict)
        self.assertIsInstance(serialized_dict["messages"], list)
        self.assertEqual(len(serialized_dict["messages"]), 3)
        self.assertEqual(serialized_dict["messages"][0]["content"], "This is a system message")
        self.assertEqual(serialized_dict["metadata"]["nested_message"]["content"], "This is a system message")
        
        # Check that it can be serialized to JSON
        try:
            json_string = json.dumps(serialized_dict)
            self.assertTrue(isinstance(json_string, str) and len(json_string) > 0)
        except Exception as e:
            self.fail(f"JSON serialization failed: {str(e)}")

if __name__ == "__main__":
    unittest.main()
