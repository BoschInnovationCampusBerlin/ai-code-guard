"""GitHub repository handler."""

import os
import tempfile
import shutil
from typing import Dict, List, Optional
import github
from github import Github
from urllib.parse import urlparse
from app.utils.config import get_github_token, get_data_dir

class GitHubHandler:
    """Handler for GitHub repositories."""
    
    def __init__(self):
        """Initialize the handler."""
        self.token = get_github_token()
        # If token is None, Github client will use unauthenticated access for public repos
        self.g = Github(self.token) if self.token else Github()
        self.repos_dir = os.path.join(get_data_dir(), "repos")
        
        if not os.path.exists(self.repos_dir):
            os.makedirs(self.repos_dir)
    
    def parse_repo_url(self, url: str) -> Dict[str, str]:
        """Parse GitHub repository URL.
        
        Args:
            url: The GitHub repository URL.
            
        Returns:
            Dict containing owner and repo name.
        """
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
            
        owner, repo = path_parts[0], path_parts[1]
        return {"owner": owner, "repo": repo}
    
    def download_repo(self, url: str, branch: str = "main") -> str:
        """Download repository files.
        
        Args:
            url: The GitHub repository URL.
            branch: The branch to download.
            
        Returns:
            Path to the downloaded repository.
        """
        import requests
        import zipfile
        import io
        
        repo_info = self.parse_repo_url(url)
        owner, repo_name = repo_info["owner"], repo_info["repo"]
        
        # Create a directory for the repository
        repo_path = os.path.join(self.repos_dir, f"{owner}_{repo_name}")
        
        # If the repo directory already exists, remove it
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            
        os.makedirs(repo_path)
        
        try:
            # For public repositories, we can download a zip file directly
            # This approach doesn't require authentication
            zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/{branch}.zip"
            print(f"Downloading zip from: {zip_url}")
            
            # Download the zip file
            response = requests.get(zip_url, stream=True)
            if response.status_code == 404:
                # Try alternative default branch names
                for alt_branch in ["master", "main", "develop"]:
                    if alt_branch != branch:
                        alt_zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/{alt_branch}.zip"
                        print(f"Trying alternative branch: {alt_branch}")
                        response = requests.get(alt_zip_url, stream=True)
                        if response.status_code == 200:
                            branch = alt_branch
                            break
            
            if response.status_code != 200:
                raise ValueError(f"Failed to download repository: HTTP status {response.status_code}")
            
            # Extract the zip file
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                zip_ref.extractall(self.repos_dir)
            
            # The zipfile creates a folder with the format "repo-branch"
            # We need to rename it to match our expected format
            extracted_dir = os.path.join(self.repos_dir, f"{repo_name}-{branch}")
            if os.path.exists(extracted_dir):
                # If repo_path exists at this point, it's empty (we created it), so we can remove it
                if os.path.exists(repo_path):
                    os.rmdir(repo_path)
                # Rename the extracted directory to our expected format
                os.rename(extracted_dir, repo_path)
            else:
                raise FileNotFoundError(f"Expected directory not found: {extracted_dir}")
            
            return repo_path
            
        except Exception as e:
            print(f"Error downloading repository: {e}")
            raise
    
    def get_repo_structure(self, repo_path: str) -> List[str]:
        """Get the file structure of the repository.
        
        Args:
            repo_path: Path to the repository.
            
        Returns:
            List of file paths in the repository.
        """
        file_paths = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.startswith('.'):
                    continue
                    
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                file_paths.append(rel_path)
                
        return file_paths
    
    def get_file_content(self, repo_path: str, file_path: str) -> Optional[str]:
        """Get the content of a file.
        
        Args:
            repo_path: Path to the repository.
            file_path: Path to the file relative to the repository root.
            
        Returns:
            Content of the file or None if the file doesn't exist or can't be read.
        """
        full_path = os.path.join(repo_path, file_path)
        
        if not os.path.exists(full_path):
            return None
            
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
