# 足球竞彩分析系统 - 架构设计

## 1. 系统总览

每日 11:30 定时任务：
1. **拉取体彩数据**：从竞彩官网 API 拉取当日全部足球赛事 + 官方赔率
2. **阶段A 赔率盲分析**：优先用 football-data skill 获取比赛基本面数据（近期战绩、排名、主客场、伤停等），不看赔率先做独立判断
3. **阶段B 赔率后验**：再结合体彩官方赔率，计算去水概率，与阶段A判断对比
4. **综合推荐**：给出一单或多单 2串1×N 组合（如 3串1、5串1+3串1）
5. **自动复盘**：第二天拉新数据前，先拉取前一天赛果，对比预测，生成复盘报告
6. **数据记录**：所有预测、结果、胜率写入 GitHub 仓库，Dashboard 可视化，可按赛事筛选

## 2. 数据源

| 数据 | 来源 | 说明 |
|------|------|------|
| 赛程+赔率 | `https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001` | 返回近3天赛事，含 HAD(胜平负)、HHAD(让球胜平负) 赔率 |
| 赛果 | `https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry?clientCode=3001&matchBeginDate=...&matchEndDate=...` | 返回比分、winFlag(H/D/A) |
| 单场完整赔率 | `https://webapi.sporttery.cn/gateway/uniform/football/getFixedBonusV1.qry?clientCode=3001&matchId=X` | 比分、总进球、半全场等全玩法 |
| 球队基本面 | football-data skill (sports-skills CLI) | ESPN 数据：近期战绩、排名、xG 等 |

### API 请求要点
- Headers 必须带 `User-Agent`、`Referer: https://www.sporttery.cn/`、`Origin: https://www.sporttery.cn`
- 路径是 `/gateway/uniform/football/...`（不是 `/gateway/jc/football/...`，后者 403）
- 无鉴权，直接 GET 即可

## 3. 数据模型

### prediction record (每次分析记录)
```json
{
  "date": "2026-08-13",
  "analysis_date": "2026-08-13T11:30:00",
  "matches": [
    {
      "match_id": 2040831,
      "match_num": "周三001",
      "league": "欧超杯",
      "home": "巴黎圣日尔曼",
      "away": "阿斯顿维拉",
      "match_time": "2026-08-13 03:00",
      "data_analysis": {
        "tendency": "H",           // 数据盲判倾向: H/D/A
        "confidence": "high",      // high/medium/low
        "reasoning": "..."         // 数据面分析依据
      },
      "odds_analysis": {
        "had": {"h": 1.60, "d": 3.48, "a": 4.60},
        "had_fair_prob": {"h": 0.58, "d": 0.27, "a": 0.15},
        "hhad": {"h": 3.00, "d": 3.25, "a": 2.05, "goal_line": -1.0},
        "conclusion": "..."        // 结合赔率后的综合判断
      },
      "final_pick": "H",           // 最终选择
      "pick_market": "HAD",        // 玩法: HAD/HHAD
      "pick_odds": 1.60,
      "is_parlay_leg": true
    }
  ],
  "parlays": [
    {
      "name": "串关1",
      "type": "2串1",
      "legs": [{"match_num": "周三001", "pick": "H", "odds": 1.60},
               {"match_num": "周四002", "pick": "H", "odds": 1.75}],
      "total_odds": 2.80,
      "reason": "..."              // 组合逻辑
    }
  ],
  "review": {                       // 第二天复盘时填充
    "results": [...],
    "parlay_results": [
      {"name": "串关1", "hit": true, "hit_legs": 2, "total_legs": 2, "profit": 1.80}
    ],
    "analysis_quality": "...",     // 复盘总结：哪里对哪里错
    "lessons": ["..."],            // 优化点
    "review_date": "2026-08-14T11:30:00"
  }
}
```

### 文件结构
```
D:\AI\hermes-studio\workSpace\football\
├── scripts/
│   ├── fetch_sporttery.py      # 拉取体彩赛程/赔率/赛果
│   ├── predict_pipeline.py     # 分析流程编排（供 cron 调用）
│   ├── review_pipeline.py      # 复盘流程
│   ├── build_dashboard.py      # 生成 Dashboard 数据 + 推送 GitHub
│   └── deploy_github.py        # GitHub API 上传（token 从 env 读）
├── data/
│   ├── raw/                     # 原始体彩数据
│   │   ├── matches_2026-08-13.json
│   │   └── results_2026-08-13.json
│   ├── predictions/             # 每次预测记录
│   │   └── 2026-08-13.json
│   └── ledger.json              # 总账本（索引所有记录）
├── dashboard/
│   ├── index.html               # GitHub Pages 看板
│   └── data.json                # 看板数据（由 build_dashboard 生成）
└── README.md
```

## 4. GitHub 部署

- 仓库：`wuyongli1/football-predictions`（GitHub Pages 公开）
- Token：`C:\Users\Administrator\.openclaw\workspace\.env.local` 的 GITHUB_TOKEN（已验证有效）
- 页面：`https://wuyongli1.github.io/football-predictions/`
- 每次分析完成后，自动 push 预测记录 + 更新 dashboard

## 5. 串关策略（2串1×N）

用户要求"2串1×N 多串组合"：
- 从当日所有比赛里选出 3-5 场高置信度比赛
- 生成多组 2串1（两两组合），或 2串1 保底 + 3串1/4串1 博高赔
- 每串注明理由和总赔率
- 单串失误即全单失效的风险提示

## 6. 复盘机制

- 每天分析前，先拉取前一天 `matchBeginDate=昨天&matchEndDate=今天` 的赛果
- 对比预测记录里的 `final_pick` 与赛果 `winFlag`
- 计算：串关命中数、胜率、赔率回报
- 生成复盘报告：哪些判断对了、哪些错了、错在哪（数据面/赔率面/运气）
- 将复盘写入预测记录，供 Dashboard 展示

## 7. 定时任务

Hermes cron（本地一直运行）：
- 每天 11:30 触发
- 流程：复盘昨天 → 拉今天数据 → 分析 → 生成预测 → 更新看板 → 推送 GitHub
- 参考技能：football-analysis-workflow、scheduled-decision-delivery-resilience
