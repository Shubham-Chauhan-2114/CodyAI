# git_utils.py
import os
import subprocess
import requests

def get_repo_size(repo_url: str) -> float:
    """Check GitHub repo size in MB via API."""
    from urllib.parse import urlparse
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip("/").replace(".git", "").split("/")
    if len(path_parts) < 2:
        raise ValueError("Invalid GitHub repo URL")

    owner, repo = path_parts[0], path_parts[1]
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    response = requests.get(api_url)
    response.raise_for_status()
    size_kb = response.json().get("size", 0)
    return round(size_kb / 1024, 2)  # MB


def clone_repo(repo_url: str, max_size_mb: int = 200) -> str:
    """Clone GitHub repo into current directory if size is within cap."""
    size_mb = get_repo_size(repo_url)
    print(f"[DEBUG] Repo size: {size_mb:.2f} MB")

    if size_mb > max_size_mb:
        raise Exception(f"Repo too large! {size_mb:.2f} MB > {max_size_mb} MB limit")

    repo_name = os.path.basename(repo_url).replace(".git", "")
    print(f"[DEBUG] Cloning repo into: {repo_name}")
    subprocess.run(["git", "clone", repo_url], check=True)

    return os.path.abspath(repo_name)
