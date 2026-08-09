# -*- coding: utf-8 -*-
"""体彩官网竞彩足球 API 封装。

数据源：中国体育彩票 sporttery.cn 竞彩足球计算器接口。
每个玩法（胜平负/让球胜平负/比分/总进球/半全场）需单独请求，
再按 matchId 合并成完整的单场数据。

用法：
    from lib.lottery import fetch_all
    matches = fetch_all()  # 当天在售全部竞彩足球比赛（五玩法合并）
"""
import json
import time
import urllib.request
import urllib.error

# 体彩竞彩足球计算器接口
SPORTTERY_URL = (
    "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry"
    "?poolCode={pool}&channel=c"
)

# 必须带 Referer，否则返回 HTML 验证页
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://www.sporttery.cn/jc/jsq/jczq/",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.sporttery.cn",
}

# 五个玩法 poolCode
POOL_CODES = ["had", "hhad", "crs", "ttg", "hafu"]

# 玩法中文名
POOL_CN = {
    "had": "胜平负",
    "hhad": "让球胜平负",
    "crs": "比分",
    "ttg": "总进球",
    "hafu": "半全场",
}


def _http_get(url, timeout=20, retries=2):
    """带重试的 GET，返回文本。"""
    last_err = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            if i < retries:
                time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"请求失败 {url}: {last_err}")


def fetch_pool(pool_code):
    """抓单个玩法的全部在售比赛。

    返回 list[dict]，每个 dict 是一场比赛的原始 subMatch 数据。
    """
    url = SPORTTERY_URL.format(pool=pool_code)
    text = _http_get(url)
    data = json.loads(text)
    if not data.get("success"):
        raise RuntimeError(f"体彩接口返回失败: {data.get('errorMessage')}")
    matches = []
    for group in data["value"]["matchInfoList"]:
        for m in group.get("subMatchList", []):
            matches.append(m)
    return matches


def _safe_odds(d, keys):
    """从 dict 中提取指定 key 的赔率，缺失返回 None。"""
    if not d:
        return {}
    return {k: d.get(k) for k in keys if k in d}


def _parse_match(raw):
    """把体彩原始 subMatch 解析成结构化比赛数据。"""
    league_slug = None
    # 延迟导入避免循环依赖
    try:
        from lib.league_map import get_league_slug
        league_slug = get_league_slug(raw.get("leagueAbbName"))
    except Exception:
        pass

    return {
        "matchId": raw.get("matchId"),
        "matchNum": raw.get("matchNum"),
        "matchNumStr": raw.get("matchNumStr"),
        "league": {
            "abbr": raw.get("leagueAbbName"),
            "name": raw.get("leagueAllName"),
            "code": raw.get("leagueCode"),
            "id": raw.get("leagueId"),
        },
        "home": {
            "id": raw.get("homeTeamId"),
            "name": raw.get("homeTeamAbbName"),
            "full_name": raw.get("homeTeamAllName"),
            "abb_en": raw.get("homeTeamAbbEnName"),
            "code": raw.get("homeTeamCode"),
            "rank": raw.get("homeRank"),
        },
        "away": {
            "id": raw.get("awayTeamId"),
            "name": raw.get("awayTeamAbbName"),
            "full_name": raw.get("awayTeamAllName"),
            "abb_en": raw.get("awayTeamAbbEnName"),
            "code": raw.get("awayTeamCode"),
            "rank": raw.get("awayRank"),
        },
        "schedule": {
            "businessDate": raw.get("businessDate"),
            "matchDate": raw.get("matchDate"),
            "matchTime": raw.get("matchTime"),
            "matchWeek": raw.get("matchWeek"),
            "status": raw.get("matchStatus"),
        },
        "odds": {
            "had": _parse_had(raw.get("had")),
            "hhad": _parse_hhad(raw.get("hhad")),
            "crs": _parse_crs(raw.get("crs")),
            "ttg": _parse_ttg(raw.get("ttg")),
            "hafu": _parse_hafu(raw.get("hafu")),
        },
        "covered": league_slug is not None,
        "league_slug": league_slug,
        "raw_pool_list": raw.get("poolList", []),
    }


def _parse_had(d):
    """胜平负：h/d/a。"""
    if not d:
        return None
    return {
        "h": d.get("h"),
        "d": d.get("d"),
        "a": d.get("a"),
    }


def _parse_hhad(d):
    """让球胜平负：h/d/a + goalLine(让球数)。"""
    if not d:
        return None
    return {
        "goalLine": d.get("goalLine"),
        "goalLineValue": d.get("goalLineValue"),
        "h": d.get("h"),
        "d": d.get("d"),
        "a": d.get("a"),
    }


def _parse_crs(d):
    """比分：key 为 4 位编码（如 0100=0:0, 1001=1:0, 0001=0:1）。"""
    if not d:
        return None
    out = {}
    for k, v in d.items():
        # 过滤非赔率字段
        if k in ("goalLine", "goalLineValue", "updateDate", "updateTime"):
            continue
        if v and v not in ("0", 0):
            out[k] = v
    return out


def _parse_ttg(d):
    """总进球：s0~s7（0球~7+球）。"""
    if not d:
        return None
    out = {}
    for i in range(8):
        key = f"s{i}"
        val = d.get(key)
        if val and val not in ("0", 0):
            out[key] = val
    return out


def _parse_hafu(d):
    """半全场：hh/hd/ha/dh/dd/da/ah/ad/aa 9 种（半场结果+全场结果）。"""
    if not d:
        return None
    keys = ["hh", "hd", "ha", "dh", "dd", "da", "ah", "ad", "aa"]
    out = {}
    for k in keys:
        val = d.get(k)
        if val and val not in ("0", 0):
            out[k] = val
    return out


def fetch_all(date_str=None):
    """抓取全部五玩法并按 matchId 合并。

    Args:
        date_str: 指定 businessDate 过滤（如 '2026-08-10'）。None 表示全部在售。

    Returns:
        dict: {
            "fetch_time": ISO 时间,
            "pools_ok": [成功玩法],
            "matches": [合并后的比赛列表],
            "covered_count": 覆盖联赛比赛数,
        }
    """
    # 以 matchId 为主键合并
    merged = {}
    pools_ok = []

    for pool in POOL_CODES:
        try:
            raw_list = fetch_pool(pool)
            pools_ok.append(pool)
        except Exception as e:
            # 单玩法失败不阻断整体（比分/半全场等不一定每场都开售）
            print(f"[warn] 玩法 {pool} 抓取失败: {e}")
            continue

        for raw in raw_list:
            mid = raw.get("matchId")
            if mid is None:
                continue
            if date_str and raw.get("businessDate") != date_str:
                continue
            if mid not in merged:
                merged[mid] = _parse_match(raw)
            else:
                # 合并该玩法的赔率到已有记录
                existing = merged[mid]
                new_odds = _parse_match(raw)["odds"][pool]
                if new_odds is not None:
                    existing["odds"][pool] = new_odds

    matches = list(merged.values())
    # 按开赛时间排序
    matches.sort(
        key=lambda m: (
            m["schedule"].get("matchDate", ""),
            m["schedule"].get("matchTime", ""),
        )
    )
    covered_count = sum(1 for m in matches if m["covered"])

    return {
        "fetch_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "pools_ok": pools_ok,
        "pools_failed": [p for p in POOL_CODES if p not in pools_ok],
        "total_count": len(matches),
        "covered_count": covered_count,
        "matches": matches,
    }


if __name__ == "__main__":
    result = fetch_all()
    print(f"抓取时间: {result['fetch_time']}")
    print(f"成功玩法: {result['pools_ok']}")
    print(f"失败玩法: {result['pools_failed']}")
    print(f"总比赛数: {result['total_count']}")
    print(f"覆盖联赛比赛数: {result['covered_count']}")
    print("\n覆盖联赛的比赛:")
    for m in result["matches"]:
        if m["covered"]:
            print(
                f"  {m['schedule']['matchDate']} {m['schedule']['matchTime']} "
                f"{m['league']['abbr']} {m['home']['name']} vs {m['away']['name']} "
                f"(slug={m['league_slug']})"
            )
