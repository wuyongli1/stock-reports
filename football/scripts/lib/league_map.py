# -*- coding: utf-8 -*-
"""体彩联赛名 <-> football-data league slug 映射表。

football-data skill 覆盖 13 个联赛：
  Premier League, La Liga, Bundesliga, Serie A, Ligue 1, MLS,
  Championship, Eredivisie, Primeira Liga, Serie A Brazil,
  Champions League, European Championship, World Cup.

体彩开售的联赛远不止这些（挪超/瑞典超/日韩/中超/澳超/俄超/土超/比甲等），
不在覆盖范围内的返回 None，由调用方决定跳过或降级处理。
"""

# 体彩联赛缩写 -> football-data league slug（None 表示 football-data 不覆盖）
LEAGUE_MAP = {
    # ---- football-data 覆盖 ----
    "英超": "premier-league",
    "西甲": "la-liga",
    "德甲": "bundesliga",
    "意甲": "serie-a",
    "法甲": "ligue-1",
    "葡超": "primeira-liga",
    "荷甲": "eredivisie",
    "英冠": "championship",
    "巴甲": "serie-a-brazil",
    "美职联": "mls",
    "欧冠": "champions-league",
    "欧洲杯": "european-championship",
    "世界杯": "world-cup",
    # ---- football-data 不覆盖（返回 None，由策略决定跳过/降级）----
    "挪超": None, "瑞典超": None, "瑞典甲": None, "芬兰超": None, "冰岛超": None,
    "丹超": None, "爱超": None, "北爱超": None,
    "日职": None, "日职乙": None, "日皇杯": None, "日联杯": None,
    "韩职": None, "韩K2": None, "韩足总杯": None,
    "中超": None, "中甲": None, "足协杯": None,
    "澳超": None, "澳足总杯": None,
    "俄超": None, "乌超": None, "罗超": None, "以超": None,
    "土超": None, "土甲": None, "阿超": None, "沙地联": None, "卡塔尔联": None,
    "比甲": None, "奥超": None, "瑞士超": None, "捷甲": None, "匈甲": None,
    "波兰超": None, "希腊超": None, "塞浦甲": None, "克罗地亚甲": None,
    "美乙": None, "智利甲": None, "阿根廷甲": None, "阿根廷乙": None,
    "哥伦比亚甲": None, "秘鲁甲": None, "巴拉圭甲": None, "乌拉圭甲": None,
    "欧联杯": None, "欧会杯": None, "欧国联": None, "欧青赛": None,
    "世预赛": None, "亚预赛": None, "非预赛": None,
    "亚冠": None, "解放者杯": None, "南美杯": None,
    "国王杯": None, "联赛杯": None, "英足总杯": None, "德国杯": None,
    "法国杯": None, "意杯": None, "葡杯": None, "荷兰杯": None,
    "西乙": None, "德乙": None, "意乙": None, "法乙": None, "葡甲": None,
    "荷乙": None, "日丙": None,
}

# football-data 覆盖的联赛 slug -> 中文（反向，用于展示页）
SLUG_TO_CN = {v: k for k, v in LEAGUE_MAP.items() if v is not None}

# 覆盖的 league slug 列表
COVERED_SLUGS = [v for v in LEAGUE_MAP.values() if v is not None]


def get_league_slug(lottery_abbr):
    """体彩联赛缩写 -> football-data slug；不覆盖返回 None。"""
    if not lottery_abbr:
        return None
    return LEAGUE_MAP.get(lottery_abbr.strip())


def is_covered(lottery_abbr):
    """该联赛是否在 football-data 覆盖范围。"""
    return get_league_slug(lottery_abbr) is not None


def slug_to_cn(slug):
    """slug -> 中文联赛名。"""
    return SLUG_TO_CN.get(slug, slug)


if __name__ == "__main__":
    # 自检：打印覆盖的联赛
    print("football-data 覆盖联赛（体彩名 -> slug）:")
    for cn, slug in LEAGUE_MAP.items():
        if slug:
            print(f"  {cn} -> {slug}")
