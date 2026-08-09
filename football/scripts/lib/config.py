# -*- coding: utf-8 -*-
"""football 项目 GitHub 发布配置。

仓库策略：暂用 wuyongli1/stock-reports 的 football/ 子目录
（现有 fine-grained token 缺建仓库权限，待用户生成新 token 后迁独立仓库）。
"""

# GitHub 仓库
OWNER = "wuyongli1"
REPO = "stock-reports"

# 仓库内子目录前缀（football 项目所有文件都在此目录下）
REMOTE_PREFIX = "football"

# 默认分支
DEFAULT_BRANCH = "main"

# GitHub Pages 根地址（stock-reports 已启用 Pages）
PAGES_BASE = "https://wuyongli1.github.io/stock-reports"

# football 子站访问入口
PAGES_ENTRY = f"{PAGES_BASE}/{REMOTE_PREFIX}/docs/index.html"

# token 读取顺序：环境变量 > openclaw 归档的 .env.local
# （token 不写入此文件，避免泄露）
