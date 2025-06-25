"""Code analyzer for repository assessment."""

import os
import json
from typing import Dict, List, Optional, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.utils.config import get_model

class CodeAnalyzer:
    """Analyzer for repository code."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.model = get_model()
        
        # Define the analysis prompt template
        self.analyze_file_prompt = ChatPromptTemplate.from_template(
            """You are a technical expert tasked with analyzing code files to identify AI capabilities, 
            data processing methods, and potential compliance issues with AI regulations.

            Analyze the following code file and provide a detailed technical description of its functionality,
            focusing on aspects relevant to AI regulation such as:
            
            1. AI capabilities and algorithms used (if any)
            2. Data processing and analysis techniques
            3. User data collection or processing
            4. Decision-making or automation features
            5. Potential biases or fairness concerns
            6. Transparency mechanisms
            7. Safety and security measures

            File path: {file_path}
            
            ```{file_type}
            {file_content}
            ```
            
            Provide a concise but comprehensive technical assessment that would help determine compliance with AI regulations.
            Structure your response as JSON with these fields:
            - ai_capabilities: list of specific AI capabilities identified
            - data_processing: description of data processing methods
            - user_impact: how the code might affect users
            - regulatory_concerns: specific concerns related to AI regulations
            - technical_summary: overall technical description
            
            If the file is not relevant for AI regulation analysis, return a brief explanation why.
            """
        )
        
        self.summarize_repo_prompt = ChatPromptTemplate.from_template(
            """You are a technical expert tasked with analyzing a GitHub repository to identify AI capabilities,
            data processing methods, and potential compliance issues with AI regulations.
            
            I will provide you with a collection of file analyses from the repository. Your task is to:
            
            1. Synthesize these individual analyses into a comprehensive technical summary of the entire repository
            2. Identify the key AI capabilities and features of the system
            3. Determine the primary data processing methods used
            4. Assess potential impacts on users and society
            5. Highlight specific concerns that may be relevant to AI regulation
            
            Here are the file analyses:
            
            {file_analyses}
            
            Based on this information, provide:
            1. A detailed technical description of the repository's functionality
            2. A list of AI capabilities identified
            3. An assessment of potential regulatory concerns
            
            Format your response as a structured technical analysis that could be used to evaluate compliance with
            the EU AI Act. Include specific technical details and be precise about the AI capabilities.
            """
        )
    
    def get_file_extension(self, file_path: str) -> str:
        """Get the file extension.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            File extension.
        """
        _, ext = os.path.splitext(file_path)
        return ext.lstrip('.')
    
    def is_code_file(self, file_path: str) -> bool:
        """Check if the file is a code file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            True if the file is a code file, False otherwise.
        """
        # List of common code file extensions
        code_extensions = {
            'py', 'js', 'jsx', 'ts', 'tsx', 'java', 'c', 'cpp', 'h', 'hpp', 
            'cs', 'go', 'rb', 'php', 'scala', 'swift', 'rs', 'kt', 'kts',
            'html', 'css', 'scss', 'sass', 'less', 'sh', 'bash', 'r'
        }
        
        # Ignore common non-code files
        ignore_patterns = [
            'LICENSE', 'README', '.git', '.github', '.gitignore',
            '.DS_Store', '.env', '.venv', '.idea', '.vscode',
            'package-lock.json', 'yarn.lock', 'Cargo.lock', 'Gemfile.lock',
            'node_modules', 'dist', 'build', 'target'
        ]
        
        # Check if file should be ignored
        for pattern in ignore_patterns:
            if pattern in file_path:
                return False
        
        # Check extension
        ext = self.get_file_extension(file_path)
        return ext in code_extensions
    
    def analyze_file(self, repo_path: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Analyze a single file.
        
        Args:
            repo_path: Path to the repository.
            file_path: Path to the file relative to the repository root.
            
        Returns:
            Analysis results or None if the file is not relevant.
        """
        if not self.is_code_file(file_path):
            return None
            
        full_path = os.path.join(repo_path, file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
                
            if not file_content.strip():
                return None
                
            # Get file extension for syntax highlighting
            file_type = self.get_file_extension(file_path)
            
            # Define the chain for file analysis
            chain = (
                {"file_path": lambda _: file_path, 
                 "file_type": lambda _: file_type, 
                 "file_content": lambda _: file_content}
                | self.analyze_file_prompt
                | self.model
                | StrOutputParser()
            )
            
            # Execute the chain
            result = chain.invoke({})
            
            # Process the result
            try:
                # Try to parse JSON
                return json.loads(result)
            except json.JSONDecodeError:
                # If not valid JSON, return as text
                return {
                    "technical_summary": result,
                    "ai_capabilities": [],
                    "data_processing": "Unknown",
                    "user_impact": "Unknown",
                    "regulatory_concerns": "Unknown"
                }
                
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return None
    
    def analyze_repository(self, repo_path: str, max_files: int = 50) -> Dict[str, Any]:
        """Analyze an entire repository.
        
        Args:
            repo_path: Path to the repository.
            max_files: Maximum number of files to analyze.
            
        Returns:
            Repository analysis results.
        """
        file_analyses = []
        file_count = 0
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file_count >= max_files:
                    break
                    
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                
                if self.is_code_file(rel_path):
                    analysis = self.analyze_file(repo_path, rel_path)
                    if analysis:
                        file_analyses.append({
                            "file_path": rel_path,
                            "analysis": analysis
                        })
                        file_count += 1
        
        # Format the file analyses for the summarization prompt
        formatted_analyses = "\n\n".join([
            f"File: {analysis['file_path']}\n" +
            f"Analysis: {json.dumps(analysis['analysis'], indent=2)}"
            for analysis in file_analyses
        ])
        
        # Define the chain for repository summarization
        chain = (
            {"file_analyses": lambda _: formatted_analyses}
            | self.summarize_repo_prompt
            | self.model
            | StrOutputParser()
        )
        
        # Execute the chain
        summary = chain.invoke({})
        
        return {
            "repository_summary": summary,
            "file_analyses": file_analyses
        }
