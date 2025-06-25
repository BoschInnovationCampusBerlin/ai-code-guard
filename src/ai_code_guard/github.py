import os
import re
from typing import Callable
import zipfile
import io
import sys

import requests
import subprocess
import shutil

REPOS_DIR = "repos"


def download_github_repo(url: str, status_callback: Callable[[str], None]) -> str:
    """
    Validates a GitHub repository URL and clones its source code using git.

    Args:
        url (str): The GitHub repository URL.
        branch (str): The branch to clone. Defaults to 'main'.

    Returns:
        str: Path to the cloned source code folder.

    Raises:
        ValueError: If the URL is invalid or clone fails.
    """

    # Validate GitHub repo URL
    pattern = r"^https://github\.com/([\w\-]+)/([\w\-]+)(?:\.git)?/?$"
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub repository URL.")

    # Use REPOS_DIR env variable
    repos_dir = os.environ.get("REPOS_DIR", REPOS_DIR)
    os.makedirs(repos_dir, exist_ok=True)

    user, repo = match.groups()
    repo_dir = os.path.join(repos_dir, f"{repo}")

    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    clone_url = f"https://github.com/{user}/{repo}.git"

    status_callback("Cloning repository using git...")

    try:
        subprocess.run(
            ["git", "clone", "--single-branch", clone_url, repo_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to clone repository: {e.stderr.decode().strip()}")

    status_callback("Repository cloned successfully.")

    return repo_dir


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} <github_repo_url>")
        exit(1)
    repo_url = sys.argv[1]
    try:
        extracted_path = download_github_repo(repo_url, lambda msg: print(msg))
        print(f"Repository extracted to: {extracted_path}")
    except ValueError as e:
        print(f"Error: {e}")
