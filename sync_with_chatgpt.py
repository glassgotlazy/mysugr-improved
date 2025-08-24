import os
import subprocess
import sys

# --- Configuration ---
GITHUB_REPO = "your-username/your-reponame"   # 🔴 change this
BRANCH = "main"                               # or "master"

TOKEN = os.getenv("GH_TOKEN")  # Token stored in environment variable
if not TOKEN:
    print("❌ Error: Please set GH_TOKEN environment variable first.")
    sys.exit(1)


def git_push(file_path, commit_msg="🤖 Auto-update from ChatGPT"):
    repo_url = f"https://x-access-token:{TOKEN}@github.com/{GITHUB_REPO}.git"
    try:
        subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", repo_url, BRANCH], check=True)
        print("✅ Code pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        print("❌ Git push failed:", e)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️ Usage: python sync_with_chatgpt.py <file-to-push>")
        sys.exit(1)

    file_path = sys.argv[1]
    git_push(file_path)
