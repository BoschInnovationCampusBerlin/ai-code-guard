from pathlib import Path
from typing import List, Dict
import json
from openai import AzureOpenAI
import os


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

class RepoFileAnalyzer:
    def __init__(self, api_key=None, batch_size=50):
        self.batch_size = batch_size

    def get_all_files(self, repo_path):
        """Get all files from repository"""
        repo_path = Path(repo_path)
        all_files = []

        for path in repo_path.rglob('*'):
            if path.is_file():
                all_files.append(str(path))

        return all_files

    def process_batch(self, file_paths: List[str]) -> Dict:
        """Process a batch of file paths"""
        # Format file paths as a string


        # Format file paths for the prompt
        files_str = "\n".join(f"- {f}" for f in file_paths)

        # Prepare the prompt
        prompt = f"""
        Given the following list of file paths, identify and categorize them into:
        1. README/Documentation files (including variations like README.md, readme.txt, etc.)
        2. Dependency specification files (including variations like requirements.txt, req.txt, requirements-dev.txt, pyproject.toml, package.json, etc.)

        Consider that file names might vary, for example:
        - 'req.txt' or 'requirements-dev.txt' instead of 'requirements.txt'
        - 'readme.rst' or 'README' instead of 'README.md'
        - 'deps.txt' might be a requirements file
        - 'project.toml' might be a pyproject.toml equivalent

        Please categorize these files:

        {files_str}

        Return the results in this JSON format:
            - "documentation_files": [list of paths],
            - "dependency_files": [list of paths],
            - "reasoning": "explanation of why certain ambiguous files were classified as they were"
            
        Return ONLY valid JSON, no additional text or markdown formatting.
        """


        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a repository structure analyzer specialized in identifying documentation and dependency files. You should be aware of various naming conventions and variations in how these files might be named."
                    },
                    {
                        "role": "user",
                        "content": prompt.format(files=files_str)
                    }
                ],
                model="hackathon-gpt-4.1",
                temperature=1  # Low temperature for more consistent results
            )
            # Get the response content
            response_content = response.choices[0].message.content.strip()
            return json.loads(response_content)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response_content}")
            return {"documentation_files": [], "dependency_files": []}
        except Exception as e:
            return f"Error in LLM classification: {str(e)}"

    def analyze_repository(self, repo_path):
        """Main method to analyze repository files"""
        # Get all files
        all_files = self.get_all_files(repo_path)

        # Skip certain directories and files
        filtered_files = [
            f for f in all_files
            if not any(skip in f for skip in [
                '/.git/', '/node_modules/', '/__pycache__/',
                '/.venv/', '/venv/', '.pyc'
            ])
        ]

        # Process files in batches
        all_results = {
            "documentation_files": [],
            "dependency_files": []
        }

        # Process in batches
        for i in range(0, len(filtered_files), self.batch_size):
            batch = filtered_files[i:i + self.batch_size]
            print(f"\nProcessing batch {i // self.batch_size + 1} ({len(batch)} files)...")

            batch_results = self.process_batch(batch)

            # Merge results
            all_results["documentation_files"].extend(batch_results["documentation_files"])
            all_results["dependency_files"].extend(batch_results["dependency_files"])

        # Remove duplicates while preserving order
        all_results["documentation_files"] = list(dict.fromkeys(all_results["documentation_files"]))
        all_results["dependency_files"] = list(dict.fromkeys(all_results["dependency_files"]))

        return all_results
        # Get LLM classification
        classification = self.classify_files_with_llm(filtered_files)

        return classification


if __name__ == "__main__":
    # Initialize analyzer
    analyzer = RepoFileAnalyzer(batch_size=50)

    # Analyze repository
    repo_path = "C:/Users/stf2bg/Desktop/ai-code-guard/repos"
    results = analyzer.analyze_repository(repo_path)

    # Print results in a formatted way
    print("\nFinal Repository Analysis Results:")
    print("=" * 50)

    print(f"\nDocumentation Files ({len(results['documentation_files'])}):")
    for doc_file in results["documentation_files"]:
        print(f"- {doc_file}")

    print(f"\nDependency Files ({len(results['dependency_files'])}):")
    for dep_file in results["dependency_files"]:
        print(f"- {dep_file}")

    # Save results as JSON
    with open('repo_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nTotal files analyzed: {sum(len(v) for v in results.values())}")