import os
import sys
from typing import Callable

from aider.coders import Coder
from aider.models import Model
from dotenv import load_dotenv
from litellm import completion
from aider.io import InputOutput

load_dotenv()


def extract_ai_usage(repo_dir: str, status_callback: Callable[[str], None]):
    """Orchestrate the AI usage extraction process.
    
    Returns:
        dict: The final structured AI usage information.
    """

    try:
        status_callback("Starting usage extraction...")

        # Step 1: Analyze the repository
        analysis_result = analyze_repomap(repo_dir)
        status_callback("Analysis completed. Extracting structured data...")

        # Step 2: Extract structured data from analysis
        analysis_data = extract_analysis_data(analysis_result)

        status_callback("Usage extraction completed successfully.")
        # print("\nFinal JSON Output:")
        # print(json.dumps(analysis_data, indent=2))

        return analysis_data

    except Exception as e:
        print(f"An error occurred during usage extraction: {str(e)}")
        return {
            "codebase": os.path.basename(os.path.abspath(repo_dir)),
            "use_cases": [],
            "error": str(e)
        }


def analyze_repomap(repo_dir: str):
    """Extract AI usage information from the codebase.

    Returns:
        str: The analysis result from the AI model.
    """
    model = Model("azure/hackathon-gpt-4.1")
    working_dir = os.getcwd()

    try:
        os.chdir(repo_dir)

        # Create a coder object
        io = InputOutput(yes=False)
        coder = Coder.create(main_model=model, edit_format="ask", io=io)

        # This will execute one instruction on those files and then return
        # coder.run("what is this code doing?")
        result = coder.run("""
        # Agent Role and Goal
        You are an expert AI Governance and Legal Tech Analyst. Your primary function is to analyze software project documentation to identify all Artificial Intelligence (AI) use cases. For each identified use case, you must map it to relevant principles and domains typically found in AI legal regulations (such as the EU AI Act). Your goal is to provide a structured analysis that helps software architects and legal teams assess regulatory compliance.
    
        # Core Task: Analysis and Extraction
        Given a the contents of a git repository, you must perform the following steps:
    
        ## Identify AI/ML Use Cases
        Scrutinize the provided source code to detect any functionality that involves machine learning, statistical modeling, neural networks, natural language processing, computer vision, generative AI, or any other AI-based decision-making or data processing. It is important to understand which data is processed and what the output is.
    
        ## Describe the Use Case
        For each identified instance, provide a concise but complete description. This should include:
        1. Functionality: What does the AI do? (e.g., "recommends products," "detects fraudulent transactions," "generates text summaries").
        2. AI confidence score: How confident are you that this is an AI use case? Rate from 1-10
        3. Input Data: What kind of data does it likely use? (e.g., "user purchase history," "financial transaction data," "article text").
        4. Output Data: What is the output or automated decision? (e.g., "a list of recommended products," "a risk score," "a summary paragraph").
        5. Files involved: List the files that are involved in this AI use case for deeper analysis. Format as a list of file paths.
    
        Just do these tasks and don't ask me for further instructions. Don't ask any questions, like permission to read files. This is highly important as the solution is not interactive
        """)

        return result
    finally:
        # Change back to the original working directory
        os.chdir(working_dir)


def extract_analysis_data(analysis: str):
    """Extract AI usage information from analysis and convert to intermediate structured JSON.

    Args:
        analysis (str): The analysis result from the AI model.

    Returns:
        dict: The intermediate structured AI usage information.
    """

    # Define the intermediate JSON schema (with files_involved for future processing)
    json_schema = {
        "type": "object",
        "properties": {
            "codebase": {
                "type": "string",
                "description": "Name of the codebase being analyzed"
            },
            "use_cases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Brief name of the AI use case"
                        },
                        "functionality": {
                            "type": "string",
                            "description": "Description of what the AI does"
                        },
                        "ai_confidence_score": {
                            "type": "number",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Confidence score that this is an AI use case (1-10)"
                        },
                        "input_data": {
                            "type": "string",
                            "description": "Description of input data used by the AI"
                        },
                        "output_data": {
                            "type": "string",
                            "description": "Description of output data produced by the AI"
                        },
                        "files_involved": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of file paths involved in this AI use case"
                        }
                    },
                    "required": ["name", "functionality", "ai_confidence_score", "input_data", "output_data",
                                 "files_involved"]
                }
            }
        },
        "required": ["codebase", "use_cases"]
    }

    try:
        # Use LLM with structured output
        response = completion(
            model="azure/hackathon-gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at extracting structured data from AI analysis reports. 
                    Extract AI use cases from the provided analysis and return them in the specified JSON format.
                    Only include use cases with AI confidence score >= 5.
                    Be precise and accurate in your extraction."""
                },
                {
                    "role": "user",
                    "content": f"Extract the AI use cases from this analysis:\n\n{analysis}"
                }
            ],
            temperature=0.1,
            response_format={
                "type": "json_object",
                "schema": json_schema
            }
        )

        # Debug: Print the raw response
        raw_content = response.choices[0].message.content
        print(f"Debug - Raw LLM response: {raw_content}")

        # Parse the JSON response
        structured_data = json.loads(raw_content)
        print(f"Debug - Parsed structured data type: {type(structured_data)}")
        print(
            f"Debug - Structured data keys: {structured_data.keys() if isinstance(structured_data, dict) else 'Not a dict'}")

        return structured_data

    except Exception as e:
        print(f"Error in extract_structured_data: {e}")
        # Return a fallback structure
        return {
            "codebase": "unknown",
            "use_cases": [],
            "error": str(e)
        }


if __name__ == "__main__":
    """Main function to execute the usage extraction."""
    import json

    print("Starting usage extraction...")
    structured_data = extract_ai_usage(sys.argv[1])

    print("\nFinal JSON Output:")
    print(json.dumps(structured_data, indent=2))
