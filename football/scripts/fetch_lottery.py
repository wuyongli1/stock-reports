# -*- coding: utf-8 -*-
"""抓取当天体彩竞彩足球全玩法数据，写入 data/raw/YYYY-MM-DD.json。

用法：
    python scripts/fetch_lottery.py
"""
import os
import sys
import json
import datetime

# 把 scripts 目录加入 path，使 from lib.xxx 可用
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib.lottery import fetch_all

# data/raw 目录（相对 scripts/ 的上级 data）
DATA_DIR = os.path.abspath(os.path.join(HERE, "..", "data", "raw"))


def main(target_date=None):
    """抓取并落盘。

    Args:
        target_date: 指定 businessDate 过滤；None 表示当天全部在售。
    """
    today = target_date or datetime.date.today().isoformat()
    print(f"[fetch] 开始抓取体彩竞彩足球（日期 {today}）...")
    result = fetch_all(date_str=None)  # 抓全部在售，不过滤日期

    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, f"{today}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[OK] 已写入 {out_path}")
    print(f"  抓取时间: {result['fetch_time']}")
    print(f"  成功玩法: {result['pools_ok']}")
    print(f"  失败玩法: {result['pools_failed']}")
    print(f"  总比赛数: {result['total_count']}")
    print(f"  覆盖联赛比赛数: {result['covered_count']}")
    print(f"  覆盖联赛明细:")
    for m in result["matches"]:
        if m["covered"]:
            print(
                f"    {m['schedule']['matchDate']} {m['schedule']['matchTime']} "
                f"{m['league']['abbr']} {m['home']['name']} vs {m['away']['name']} "
                f"(slug={m['league_slug']})"
            )
    return out_path


if __name__ == "__main__":
    # 支持命令行传日期参数
    arg_date = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg_date)
