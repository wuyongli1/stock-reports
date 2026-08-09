# -*- coding: utf-8 -*-
"""GitHub Git Database API 封装：一次性提交多个文件（一个 commit）。

用 blobs + trees + commits + refs 流程，避免逐文件 contents API 的低效，
也不需要克隆整个仓库。适合把 football/ 子目录全量推送到 stock-reports。
"""
import os
import json
import urllib.request
import urllib.error

API_BASE = "https://api.github.com"

# token 读取顺序
_TOKEN_CANDIDATES = [
    os.environ.get("GITHUB_TOKEN"),
    os.environ.get("GH_TOKEN"),
]


def _load_token():
    """按优先级读取 GitHub token。"""
    for t in _TOKEN_CANDIDATES:
        if t:
            return t
    # fallback: openclaw 归档的 .env.local
    env_path = os.path.expanduser(
        "~/.workbuddy/openclaw-archive/config/.env.local"
    )
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    return line.split("=", 1)[1].strip()
    raise RuntimeError(
        "未找到 GITHUB_TOKEN。请设置环境变量 GITHUB_TOKEN，"
        "或确认 ~/.workbuddy/openclaw-archive/config/.env.local 存在。"
    )


class GitHubRepo:
    def __init__(self, owner, repo, token=None, branch="main"):
        self.owner = owner
        self.repo = repo
        self.token = token or _load_token()
        self.branch = branch

    def _api(self, method, path, data=None):
        url = f"{API_BASE}/repos/{self.owner}/{self.repo}/{path}"
        body = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "football-predict-publisher",
        }
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                text = resp.read().decode("utf-8")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {method} {path} 失败 {e.code}: {err_body}") from e

    def _head_ref(self):
        ref = self._api("GET", f"git/refs/heads/{self.branch}")
        return ref["object"]["sha"]

    def _commit_tree(self, commit_sha):
        commit = self._api("GET", f"git/commits/{commit_sha}")
        return commit["tree"]["sha"]

    def _create_blob(self, content):
        blob = self._api("POST", "git/blobs", {"content": content, "encoding": "utf-8"})
        return blob["sha"]

    def _create_tree(self, base_tree_sha, tree_items):
        # GitHub 单次 tree 最多 500 条目，分批
        if len(tree_items) <= 500:
            new_tree = self._api(
                "POST", "git/trees",
                {"base_tree": base_tree_sha, "tree": tree_items},
            )
            return new_tree["sha"]
        # 分批
        cur_base = base_tree_sha
        for i in range(0, len(tree_items), 500):
            batch = tree_items[i:i + 500]
            new_tree = self._api(
                "POST", "git/trees",
                {"base_tree": cur_base, "tree": batch},
            )
            cur_base = new_tree["sha"]
        return cur_base

    def _create_commit(self, parent_sha, tree_sha, message):
        commit = self._api(
            "POST", "git/commits",
            {"message": message, "tree": tree_sha, "parents": [parent_sha]},
        )
        return commit["sha"]

    def _update_ref(self, sha):
        self._api("PATCH", f"git/refs/heads/{self.branch}", {"sha": sha})

    def push_files(self, files, commit_msg):
        """一次性推送多个文件。

        Args:
            files: [{"path": "football/xxx.py", "content": "..."}, ...]
            commit_msg: commit 信息

        Returns:
            新 commit 的 sha
        """
        if not files:
            raise RuntimeError("无文件可推送")

        print(f"[github] 推送 {len(files)} 个文件到 {self.owner}/{self.repo}...")
        parent_sha = self._head_ref()
        base_tree = self._commit_tree(parent_sha)

        # 创建 blobs
        tree_items = []
        for i, f in enumerate(files):
            blob_sha = self._create_blob(f["content"])
            tree_items.append({
                "path": f["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            })
            if (i + 1) % 20 == 0:
                print(f"  blob {i + 1}/{len(files)}")

        new_tree = self._create_tree(base_tree, tree_items)
        new_commit = self._create_commit(parent_sha, new_tree, commit_msg)
        self._update_ref(new_commit)
        print(f"[github] 推送成功 commit={new_commit[:8]}")
        return new_commit

    def file_exists(self, path):
        """检查某文件是否已存在（用于判断首次发布）。"""
        try:
            self._api("GET", f"contents/{path}?ref={self.branch}")
            return True
        except RuntimeError:
            return False
