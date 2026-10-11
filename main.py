# -*- coding: utf-8 -*-
"""
Still Here 个人网站后端
- 唯一 API 接口：GET /api/news  —— 实时抓取四个情报源并过滤，返回干净 JSON
- 同时托管前端静态文件（test1.html、图片、数据文件）
启动：python main.py  →  http://127.0.0.1:8898/test1.html
接口文档：http://127.0.0.1:8898/docs
"""
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

MY_DIR = r"C:\Users\LEOVO\.zcode\workspace\default\my-website"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
HEADERS = {"User-Agent": UA, "Referer": "https://www.bilibili.com/"}

CACHE_TTL = 600  # 秒：10 分钟内直接返回缓存
_cache_lock = threading.Lock()
_cache = {"data": None, "ts": 0.0}

JUNK = re.compile(r"聚焦赛场|同步全球|实时查看|实时赛事|随时追踪|赛场焦点|获取最新|点击观看|限时领取|全网最低|一键三连|合集.*全集|完整版")
NBA_TEAMS = re.compile(r"NBA|WNBA|篮球|勇士|湖人|凯尔特人|独行侠|快船|雄鹿|掘金|太阳|热火|尼克斯|森林狼|骑士|雷霆|步行者|活塞|76人|篮网|老鹰|黄蜂|公牛|猛龙|魔术|奇才|开拓者|灰熊|马刺|国王|火箭|鹈鹕|爵士|库里|詹姆斯|杜兰特|文班亚马|哈登")
THU_PRI = re.compile(r"AI|人工智能|大模型|机器人|芯片|半导|核|原子|聚变|反应堆|辐射|物理|量子")

BILI_SEARCH = "https://api.bilibili.com/x/web-interface/search/type"

app = FastAPI(title="Still Here 情报站", description="每日要闻实时抓取接口")


def clean(s: str) -> str:
    """去掉 B 站搜索结果里的 <em> 高亮标签和多余空白"""
    return re.sub(r"\s+", " ", re.sub(r"</?em[^>]*>", "", s or "")).strip()


def is_junk(s: str) -> bool:
    return bool(JUNK.search(s))


def parse_rss(text: str, n: int, max_age_hours: int) -> list:
    """解析 RSS XML，按时效窗口取前 n 条"""
    out = []
    try:
        root = ET.fromstring(text)
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_hours * 3600 if max_age_hours else 0
        for item in root.iter("item"):
            title = clean(item.findtext("title") or "")
            link = (item.findtext("link") or "").strip()
            if cutoff:
                pub = item.findtext("pubDate") or ""
                try:
                    if parsedate_to_datetime(pub).timestamp() < cutoff:
                        break
                except Exception:
                    pass
            if title and link.startswith("http") and not is_junk(title):
                out.append({"t": title, "u": link})
                if len(out) >= n:
                    break
    except Exception:
        pass
    return out


def bili_items(data: dict, n: int, author_sub: str, max_age_hours: int, title_re=None) -> list:
    """从 B 站搜索 JSON 中取前 n 条（作者过滤 + 时效 + 标题正则 + 水贴过滤）"""
    out = []
    results = (data or {}).get("data", {}).get("result") or []
    cutoff = datetime.now(timezone.utc).timestamp() - max_age_hours * 3600 if max_age_hours else 0
    for r in results:
        if author_sub and author_sub not in (r.get("author") or ""):
            continue
        title = clean(str(r.get("title") or ""))
        link = str(r.get("arcurl") or "")
        pubdate = r.get("pubdate") or 0
        if max_age_hours and pubdate and pubdate < cutoff:
            break
        if title_re and not title_re.search(title):
            continue
        if title and link.startswith("http") and not is_junk(title):
            out.append({"t": title, "u": link})
            if len(out) >= n:
                break
    return out


def bili_get(client: httpx.Client, params: dict) -> dict:
    """B 站接口带一次重试（限流时返回非 JSON，稍候重试）"""
    last_err = None
    for _ in range(2):
        try:
            return client.get(BILI_SEARCH, params=params).json()
        except Exception as e:
            last_err = e
            time.sleep(1.5)
    raise last_err or RuntimeError("bilibili failed")


def fetch_source(client: httpx.Client, kind: str) -> tuple:
    """抓取单个源，返回 (key, items, failed)"""
    try:
        if kind == "ai":  # 量子位 RSS，24 小时内
            r = client.get("https://www.qbitai.com/feed")
            return kind, parse_rss(r.text, 4, 24), False

        if kind == "nba":  # B 站最新战报，36 小时内且标题须 NBA 相关
            r = bili_get(client, {"search_type": "video", "order": "pubdate", "keyword": "NBA战报"})
            return kind, bili_items(r, 4, "", 36, NBA_TEAMS), False

        if kind == "thu":  # B 站“清华大学”清华系账号，72 小时内，AI/核科学优先
            r = bili_get(client, {"search_type": "video", "order": "pubdate", "keyword": "清华大学"})
            items = bili_items(r, 12, "清华", 72)
            pri = [it for it in items if THU_PRI.search(it["t"])]
            rest = [it for it in items if not THU_PRI.search(it["t"])]
            return kind, (pri + rest)[:4], False

        if kind == "csgo_hltv":  # HLTV 国际要闻，72 小时内
            r = client.get("https://www.hltv.org/rss/news")
            return kind, parse_rss(r.text, 2, 72), False

        if kind == "csgo_up":  # CSGO-DOUBLEup 最新视频，72 小时内
            r = bili_get(client, {"search_type": "video", "order": "pubdate", "keyword": "CSGO-DOUBLEup"})
            return kind, bili_items(r, 2, "CSGO", 72), False
    except Exception:
        pass
    return kind, [], True


@app.get("/api/news", summary="实时抓取四个板块的要闻")
def get_news(force: int = 0):
    """AI(24h) / NBA(36h) / 清华科研(72h) / CS:GO(72h)，各源独立容错。
    10 分钟内重复调用直接返回缓存；?force=1 强制重新抓取。"""
    now_ts = time.time()
    with _cache_lock:
        cached = _cache["data"]
        ts = _cache["ts"]
    if cached and not force and now_ts - ts < CACHE_TTL:
        return cached

    keys = ["ai", "nba", "thu", "csgo_hltv", "csgo_up"]
    data = {}
    with httpx.Client(headers=HEADERS, timeout=12, follow_redirects=True) as client:
        with ThreadPoolExecutor(max_workers=5) as pool:
            for kind, items, failed in pool.map(lambda k: fetch_source(client, k), keys):
                data[kind] = {"items": items, "failed": failed}

    csgo = data["csgo_hltv"]["items"] + data["csgo_up"]["items"]
    now = datetime.now()
    failed = [k for k in ["ai", "nba", "thu"] if data[k]["failed"] and not data[k]["items"]]
    if not csgo and (data["csgo_hltv"]["failed"] or data["csgo_up"]["failed"]):
        failed.append("csgo")
    result = {
        "date": now.strftime("%Y-%m-%d"),
        "updated": now.strftime("%H:%M"),
        "ai": data["ai"]["items"],
        "nba": data["nba"]["items"],
        "thu": data["thu"]["items"],
        "csgo": csgo,
        "failed": failed,
    }
    with _cache_lock:
        _cache["data"] = result
        _cache["ts"] = time.time()
    return result


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(MY_DIR + r"\test1.html")


# 静态文件兜底（图片、news-data.js、philosophy-data.js 等），必须最后挂载
app.mount("/", StaticFiles(directory=MY_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8898)
