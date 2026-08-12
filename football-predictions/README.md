# ⚽ 足球竞彩每日分析预测

**数据优先分析 + 赔率后验校验 + 每日自动复盘 + 可视化看板**

> 本仓库仅记录个人分析预测与研究，不构成任何投注建议。购彩有风险，投注需理性。

---

## 📌 系统简介

每日 11:30 自动运行的分析流水线：

1. **拉取体彩数据**：从中国体育彩票竞彩官网（sporttery.cn）官方 API 拉取当日足球赛事赛程与官方赔率
2. **阶段A · 赔率盲分析**：先不看赔率，用 football-data（ESPN）基本面数据独立分析——近期战绩、主客场、排名、状态
3. **阶段B · 赔率后验**：再结合体彩官方赔率，计算去水概率，与阶段A判断交叉验证
4. **串关推荐**：给出 2串1×N 多串组合（如 2串1 保底 + 3串1 博高赔）
5. **自动复盘**：次日拉取赛果，自动对比预测，生成复盘报告，持续优化分析
6. **可视化看板**：GitHub Pages 看板展示所有预测记录，可按赛事（挪超/巴甲/法甲/英超等）筛选，统计胜率

## 📊 看板访问

**GitHub Pages（主站）**: https://wuyongli1.github.io/stock-reports/football-predictions/

**Vercel 备用站**: https://football-predictions-sandy.vercel.app/

> GitHub Pages（github.io）在中国大陆不同网络环境下连通性不稳定；Vercel 备用站是独立部署，主站打不开时使用。每日 cron 更新时会同时部署两个站，内容保持一致。

看板功能：
- 总预测场次 / 命中 / 未中 / 命中率 统计
- 串关单数 / 串关命中 / 串关胜率
- 按赛事筛选（挪超、巴甲、法甲、英超、欧冠、解放者杯...）
- 按状态筛选（命中/未中/待开赛）
- 搜索球队、比赛编号
- 每场比赛可展开查看分析详情（数据面判断 + 赔率面校验 + 复盘）

## 🏗 项目结构

```
├── scripts/
│   ├── fetch_sporttery.py      # 体彩官方数据拉取（赛程/赔率/赛果）
│   ├── update_results.py       # 赛果回填（复盘）
│   ├── save_prediction.py      # 预测记录保存
│   ├── build_dashboard.py      # Dashboard 数据聚合
│   └── deploy_github.py        # GitHub Pages 部署
├── data/
│   ├── raw/                    # 体彩原始数据
│   └── predictions/            # 每日预测记录（JSON）
├── dashboard/
│   ├── index.html              # 看板页面
│   └── data.json               # 看板数据
└── ARCHITECTURE.md             # 架构设计文档
```

## 🔧 数据源

| 数据 | API |
|------|-----|
| 赛程+赔率 | `webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry` |
| 赛果 | `webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry` |
| 单场完整赔率 | `webapi.sporttery.cn/gateway/uniform/football/getFixedBonusV1.qry` |
| 基本面数据 | football-data skill（ESPN 数据） |

## 📈 预测记录格式

每天的分析生成 `data/predictions/YYYY-MM-DD.json`，包含：
- 每场比赛：数据面分析（倾向/置信度/理由）、赔率面校验（去水概率/结论）、最终选择
- 串关组合：每串的场次、选择、综合赔率、组合理由
- 复盘（次日回填）：实际比分、命中/未中、串关结果、复盘总结

## 🚀 本地运行

```bash
# 拉取今日赛程+赔率
python scripts/fetch_sporttery.py matches

# 拉取赛果并回填
python scripts/update_results.py 3

# 生成 Dashboard 数据
python scripts/build_dashboard.py

# 部署到 GitHub Pages
python scripts/deploy_github.py push-dashboard dashboard
```

## ⚠️ 免责声明

- 本系统仅用于个人学习研究与数据记录
- 足球比赛结果受大量不可控因素影响，任何预测都存在不确定性
- 不构成任何投注建议，请理性购彩
