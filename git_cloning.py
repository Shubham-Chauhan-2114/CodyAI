import os
import subprocess
from urllib.parse import urlparse

def clone_repo(repo_url, base_dir="."):
    """
    Clone a GitHub repository into the given base directory.
    Repo folder will be named after the repo.
    """
    # Extract repo name from URL
    parsed_url = urlparse(repo_url)
    repo_name = os.path.splitext(os.path.basename(parsed_url.path))[0]

    target_path = os.path.join(base_dir, repo_name)

    if os.path.exists(target_path):
        print(f"[DEBUG] Repo already exists at: {target_path}")
        return target_path

    print(f"[DEBUG] Cloning repo {repo_url} into {target_path} ...")

    try:
        subprocess.run(
            ["git", "clone", repo_url, target_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"[DEBUG] Successfully cloned: {target_path}")
        return target_path
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to clone repo: {e.stderr.decode()}")
        return None

# Example usage
if __name__ == "__main__":
    repo_url = input("Enter GitHub repo URL: ")
    path = clone_repo(repo_url, base_dir=".")
    print("\n"+path)
