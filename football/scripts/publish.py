# -*- coding: utf-8 -*-
"""把 football/ 目录全量推送到 GitHub stock-reports/football/。

用法：
    python scripts/publish.py [commit_message]
"""
import os
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib.github import GitHubRepo
from lib.config import OWNER, REPO, REMOTE_PREFIX, PAGES_ENTRY, DEFAULT_BRANCH

FOOTBALL_DIR = os.path.abspath(os.path.join(HERE, ".."))

IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".pytest_cache"}
IGNORE_EXTS = {".pyc", ".pyo"}
IGNORE_FILES = {".env", ".env.local", "Thumbs.db", ".DS_Store"}


def collect_files(local_dir, remote_prefix):
    """遍历本地目录，收集待推送文件列表。"""
    files = []
    for root, dirs, fnames in os.walk(local_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fn in fnames:
            ext = os.path.splitext(fn)[1].lower()
            if fn in IGNORE_FILES or ext in IGNORE_EXTS:
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, local_dir).replace(os.sep, "/")
            remote_path = f"{remote_prefix}/{rel}"
            try:
                with open(full, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue
            files.append({"path": remote_path, "content": content})
    return files


def main():
    msg = (
        sys.argv[1]
        if len(sys.argv) > 1
        else f"football: 自动发布 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    files = collect_files(FOOTBALL_DIR, REMOTE_PREFIX)
    print(f"收集到 {len(files)} 个文件待推送")
    if not files:
        print("无文件，退出")
        return
    for f in files:
        print(f"  - {f['path']}")

    repo = GitHubRepo(OWNER, REPO, branch=DEFAULT_BRANCH)
    sha = repo.push_files(files, msg)
    print(f"\n发布完成")
    print(f"  commit: {sha}")
    print(f"  仓库: https://github.com/{OWNER}/{REPO}/tree/{DEFAULT_BRANCH}/{REMOTE_PREFIX}")
    print(f"  Pages: {PAGES_ENTRY}")


if __name__ == "__main__":
    main()
