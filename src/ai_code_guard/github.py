import os
import re
from typing import Callable
import zipfile
import io
import sys

import requests

REPOS_DIR = "repos"


def download_github_repo(url: str, branch: str = "main", status_callback: Callable[[str], None] = None) -> str:
    """
    Validates a GitHub repository URL and downloads its source code as a zip file.

    Args:
        url (str): The GitHub repository URL.
        branch (str): The branch to download. Defaults to 'main'.

    Returns:
        str: Path to the extracted source code folder.

    Raises:
        ValueError: If the URL is invalid or download fails.
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
    zip_url = f"https://github.com/{user}/{repo}/archive/refs/heads/{branch}.zip"

    # Download only the specified branch, do not fallback
    status_callback("Downloading repository zip file...")
    response = requests.get(zip_url)
    if response.status_code != 200:
        raise ValueError(f"Could not download repository zip file for branch '{branch}'.")

    # Extract zip file
    status_callback("Unpacking repository zip file...")
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(repos_dir)
        extracted_folder = os.path.join(repos_dir, z.namelist()[0].split("/")[0])

    status_callback("Repository downloaded and extracted successfully.")
    return extracted_folder


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} <github_repo_url> [branch]")
        exit(1)
    repo_url = sys.argv[1]
    kwargs = {}
    if len(sys.argv) > 2:
        kwargs["branch"] = sys.argv[2]
    try:
        extracted_path = download_github_repo(repo_url, **kwargs)
        print(f"Repository extracted to: {extracted_path}")
    except ValueError as e:
        print(f"Error: {e}")
