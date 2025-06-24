import json
from openai import AzureOpenAI
from pathlib import Path
import os
import time
from typing import Dict, List, Optional

os.environ['HTTP_PROXY'] = "http://localhost:3128"
os.environ['HTTPS_PROXY'] = "http://localhost:3128"

endpoint = "https://boschdemov4.openai.azure.com/openai/deployments/hackathon-gpt-4.1/chat/completions?api-version=2025-01-01-preview"

subscription_key = "b7ac5b08650e44f88baf0821f6b40d6e"
api_version = "2025-01-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

class AIDocumentationScanner:
    """Scanner for detecting AI-related content in documentation files"""

    def __init__(self, repo_analysis_path: str, api_key: Optional[str] = None):
        self.repo_analysis_path = repo_analysis_path

    def scan_documentation_for_ai(self) -> Dict:
        """
        Main method to scan documentation files for AI-related content
        """
        try:
            # Load the repository analysis
            with open(self.repo_analysis_path, 'r') as f:
                repo_data = json.load(f)

            results = {
                "files_scanned": 0,
                "files_with_ai_content": 0,
                "ai_mentions": []
            }
            # Process each documentation file
            for doc_path in repo_data.get("documentation_files", []):
                file_result = self._analyze_single_doc(doc_path)
                if file_result:
                    results["files_scanned"] += 1
                    if file_result["has_ai_content"]:
                        results["files_with_ai_content"] += 1
                        results["ai_mentions"].append(file_result)

                # Rate limiting
                time.sleep(1)

            return results

        except Exception as e:
            print(f"Error scanning documentation: {e}")
            return {"error": str(e)}

    def _analyze_single_doc(self, file_path: str) -> Optional[Dict]:
        """
        Analyze a single documentation file for AI content
        """
        try:
            print(f"Analyzing: {file_path}")

            # Read file content
            content = self._read_file_content(file_path)
            if not content:
                return None

            # Get AI analysis from LLM
            analysis = self._check_ai_content(content, file_path)
            return analysis

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def _read_file_content(self, file_path: str) -> str:
        """
        Safely read content from a file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""

    def _check_ai_content(self, content: str, file_path: str) -> Dict:
        """
        Check file content for AI-related mentions using LLM
        """
        prompt = f"""
        Analyze this documentation file and identify any mentions or indications of AI usage.
        Look for:
        1. Direct mentions of AI, machine learning, neural networks
        2. AI libraries or frameworks (e.g., TensorFlow, PyTorch)
        3. AI-related features or capabilities
        4. AI model training or usage instructions
        5. AI-related configurations

        File content:
        {content[:4000]}  # Limiting content to avoid token limits

        Return ONLY a valid JSON response:
        {{
            "file_path": "{file_path}",
            "has_ai_content": true/false,
            "ai_mentions": [
                {{
                    "type": "framework|technology|feature|configuration",
                    "mention": "specific mention",
                    "context": "brief context"
                }}
            ],
            "summary": "brief summary of AI usage in this file"
        }}
        Return ONLY valid JSON, no additional text or markdown formatting.
        """

        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI documentation analyzer. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="hackathon-gpt-4.1",
                temperature=1  # Low temperature for more consistent results
            )

            # Parse and clean response
            content = response.choices[0].message.content

            return json.loads(content.strip())

        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            return {
                "file_path": file_path,
                "has_ai_content": False,
                "ai_mentions": [],
                "summary": f"Error during analysis: {str(e)}"
            }


    def save_results(self, results: Dict, output_path: str = "ai_documentation_scan.json"):
        """
        Save scan results to a JSON file
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}")


    @staticmethod
    def print_scan_results(results: Dict):
        """
        Print scan results in a readable format
        """
        print("\nAI Documentation Scan Results")
        print("=" * 50)

        if "error" in results:
            print(f"\nError occurred during scanning: {results['error']}")
            return

        print(f"\nFiles Scanned: {results['files_scanned']}")
        print(f"Files with AI Content: {results['files_with_ai_content']}")

        if results['files_with_ai_content'] > 0:
            print("\nDetailed Findings:")
            print("-" * 30)

            for file_result in results['ai_mentions']:
                print(f"\nFile: {file_result['file_path']}")
                print(f"Summary: {file_result['summary']}")

                if file_result['ai_mentions']:
                    print("\nAI Mentions:")
                    for mention in file_result['ai_mentions']:
                        print(f"  - Type: {mention['type']}")
                        print(f"    Mention: {mention['mention']}")
                        print(f"    Context: {mention['context']}")
                print("-" * 30)


# Example usage
if __name__ == "__main__":
    # Initialize scanner
    ai_scanner = AIDocumentationScanner('repo_analysis.json')

    # Scan documentation
    scan_results = ai_scanner.scan_documentation_for_ai()

    # Print results
    AIDocumentationScanner.print_scan_results(scan_results)

    # Save results
    ai_scanner.save_results(scan_results)