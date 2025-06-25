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
    """Scanner for detecting AI-related content in documentation and dependency files"""

    def __init__(self, repo_analysis_path: str, api_key: Optional[str] = None):
        self.repo_analysis_path = repo_analysis_path

    def scan_for_ai_content(self) -> Dict:
        """
        Main method to scan both documentation and dependency files for AI-related content
        """
        try:
            # Load the repository analysis
            with open(self.repo_analysis_path, 'r') as f:
                repo_data = json.load(f)

            results = {
                "documentation_analysis": {
                    "files_scanned": 0,
                    "files_with_ai_content": 0,
                    "ai_mentions": []
                },
                "dependency_analysis": {
                    "files_scanned": 0,
                    "files_with_ai_content": 0,
                    "ai_mentions": []
                },
                "summary": {
                    "total_files_scanned": 0,
                    "total_ai_files": 0,
                    "unique_ai_technologies": set()
                }
            }

            # Process documentation files
            print("\nAnalyzing documentation files...")
            for doc_path in repo_data.get("documentation_files", []):
                file_result = self._analyze_single_file(doc_path, is_dependency=False)
                if file_result:
                    results["documentation_analysis"]["files_scanned"] += 1
                    if file_result["has_ai_content"]:
                        results["documentation_analysis"]["files_with_ai_content"] += 1
                        results["documentation_analysis"]["ai_mentions"].append(file_result)
                time.sleep(1)

            # Process dependency files
            print("\nAnalyzing dependency files...")
            for dep_path in repo_data.get("dependency_files", []):
                file_result = self._analyze_single_file(dep_path, is_dependency=True)
                if file_result:
                    results["dependency_analysis"]["files_scanned"] += 1
                    if file_result["has_ai_content"]:
                        results["dependency_analysis"]["files_with_ai_content"] += 1
                        results["dependency_analysis"]["ai_mentions"].append(file_result)
                time.sleep(1)

            # Update summary
            self._update_summary(results)

            # Convert set to list for JSON serialization
            results["summary"]["unique_ai_technologies"] = list(results["summary"]["unique_ai_technologies"])

            return results

        except Exception as e:
            print(f"Error scanning files: {e}")
            return {"error": str(e)}

    def _analyze_single_file(self, file_path: str, is_dependency: bool) -> Optional[Dict]:
        """
        Analyze a single file for AI content
        """
        try:
            print(f"Analyzing: {file_path}")

            content = self._read_file_content(file_path)
            if not content:
                return None

            if is_dependency:
                return self._check_dependency_content(content, file_path)
            return self._check_documentation_content(content, file_path)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def _check_documentation_content(self, content: str, file_path: str) -> Dict:
        """Check documentation content for AI-related mentions"""
        prompt = f"""
        Analyze this documentation file and identify any mentions or indications of AI usage.
        Look for:
        1. Direct mentions of AI, machine learning, neural networks
        2. AI libraries or frameworks (e.g., TensorFlow, PyTorch)
        3. AI-related features or capabilities
        4. AI model training or usage instructions
        5. AI-related configurations

        File content:
        {content[:4000]}

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

        return self._get_llm_analysis(prompt)

    def _check_dependency_content(self, content: str, file_path: str) -> Dict:
        """Check dependency file content for AI-related packages"""
        prompt = f"""
        Analyze this dependency file and identify any AI-related packages or libraries.
        Look for:
        1. Machine learning libraries (tensorflow, pytorch, scikit-learn, etc.)
        2. Deep learning frameworks
        3. NLP libraries (transformers, spacy, nltk, etc.)
        4. Computer vision libraries
        5. AI/ML utilities and tools
        6. Model serving dependencies
        7. LLMs
        8. Agentic AI 

        File content:
        {content[:4000]}

        Return ONLY a valid JSON response:
        {{
            "file_path": "{file_path}",
            "has_ai_content": true/false,
            "ai_mentions": [
                {{
                    "type": "library|framework|tool",
                    "mention": "package name and version",
                    "context": "purpose/usage of this AI package"
                }}
            ],
            "summary": "brief summary of AI dependencies found"
        }}
        Return ONLY valid JSON, no additional text or markdown formatting.
        """

        return self._get_llm_analysis(prompt)

    def _get_llm_analysis(self, prompt: str) -> Dict:
        """Get analysis from LLM"""
        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI content analyzer. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="hackathon-gpt-4.1",
                temperature=1
            )

            content = response.choices[0].message.content
            return json.loads(content.strip())

        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            return {
                "has_ai_content": False,
                "ai_mentions": [],
                "summary": f"Error during analysis: {str(e)}"
            }

    def _read_file_content(self, file_path: str) -> str:
        """Safely read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""

    def _update_summary(self, results: Dict) -> None:
        """Update the summary section of results"""
        # Calculate totals
        results["summary"]["total_files_scanned"] = (
                results["documentation_analysis"]["files_scanned"] +
                results["dependency_analysis"]["files_scanned"]
        )
        results["summary"]["total_ai_files"] = (
                results["documentation_analysis"]["files_with_ai_content"] +
                results["dependency_analysis"]["files_with_ai_content"]
        )

        # Collect unique AI technologies
        for analysis in ["documentation_analysis", "dependency_analysis"]:
            for file_result in results[analysis]["ai_mentions"]:
                for mention in file_result.get("ai_mentions", []):
                    results["summary"]["unique_ai_technologies"].add(mention["mention"])

    def save_results(self, results: Dict, output_path: str = "ai_scan_results.json"):
        """Save scan results to a JSON file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}")

    @staticmethod
    def print_scan_results(results: Dict):
        """Print scan results in a readable format"""
        print("\nAI Content Scan Results")
        print("=" * 50)

        if "error" in results:
            print(f"\nError occurred during scanning: {results['error']}")
            return

        # Documentation Analysis
        print("\nDocumentation Analysis:")
        print("-" * 30)
        print(f"Files Scanned: {results['documentation_analysis']['files_scanned']}")
        print(f"Files with AI Content: {results['documentation_analysis']['files_with_ai_content']}")

        if results['documentation_analysis']['ai_mentions']:
            print("\nAI Mentions in Documentation:")
            for file_result in results['documentation_analysis']['ai_mentions']:
                print(f"\nFile: {file_result['file_path']}")
                print(f"Summary: {file_result['summary']}")
                for mention in file_result['ai_mentions']:
                    print(f"  - {mention['type']}: {mention['mention']}")
                    print(f"    Context: {mention['context']}")

        # Dependency Analysis
        print("\nDependency Analysis:")
        print("-" * 30)
        print(f"Files Scanned: {results['dependency_analysis']['files_scanned']}")
        print(f"Files with AI Dependencies: {results['dependency_analysis']['files_with_ai_content']}")

        if results['dependency_analysis']['ai_mentions']:
            print("\nAI Dependencies Found:")
            for file_result in results['dependency_analysis']['ai_mentions']:
                print(f"\nFile: {file_result['file_path']}")
                print(f"Summary: {file_result['summary']}")
                for mention in file_result['ai_mentions']:
                    print(f"  - {mention['type']}: {mention['mention']}")
                    print(f"    Purpose: {mention['context']}")

        # Overall Summary
        print("\nOverall Summary:")
        print("-" * 30)
        print(f"Total Files Scanned: {results['summary']['total_files_scanned']}")
        print(f"Total Files with AI Content: {results['summary']['total_ai_files']}")

        if results['summary']['unique_ai_technologies']:
            print("\nUnique AI Technologies Found:")
            for tech in results['summary']['unique_ai_technologies']:
                print(f"- {tech}")


# Example usage
if __name__ == "__main__":
    # Initialize scanner
    scanner = AIDocumentationScanner('repo_analysis.json')

    # Scan files
    results = scanner.scan_for_ai_content()

    # Print results
    AIDocumentationScanner.print_scan_results(results)

    # Save results
    scanner.save_results(results)


# Example usage
if __name__ == "__main__":
    # Initialize scanner
    scanner = AIDocumentationScanner('repo_analysis.json')

    # Scan files
    results = scanner.scan_for_ai_content()

    # Print results
    AIDocumentationScanner.print_scan_results(results)

    # Save results
    scanner.save_results(results)