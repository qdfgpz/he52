# -*- coding: utf-8 -*-
"""
Still Here 个人网站后端
- 唯一 API 接口：GET /api/news  —— 实时抓取四个情报源并过滤，返回干净 JSON
- 同时托管前端静态文件（index.html、图片、数据文件）
启动：python main.py  →  http://127.0.0.1:8898/
接口文档：http://127.0.0.1:8898/docs
"""
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# 项目根目录：以本文件位置定位，项目挪到哪都能跑
BASE_DIR = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
HEADERS = {
    "User-Agent": UA,
    "Referer": "https://www.bilibili.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
}

CACHE_TTL = 600  # 秒：10 分钟内直接返回缓存
_cache_lock = threading.Lock()
_refresh_lock = threading.Lock()
_fetch_lock = threading.Lock()   # 抓取单飞：同一时刻只跑一轮，并发的强制刷新共用结果
_refreshing = {"v": False}
_cache = {"data": None, "ts": 0.0}
FORCE_FRESH_WINDOW = 5  # 秒：强制刷新时，缓存比这更新说明刚有另一轮抓完，直接复用

JUNK = re.compile(r"聚焦赛场|同步全球|实时查看|实时赛事|随时追踪|赛场焦点|获取最新|点击观看|限时领取|全网最低|一键三连|合集.*全集|完整版")
NBA_TEAMS = re.compile(r"NBA|WNBA|篮球|勇士|湖人|凯尔特人|独行侠|快船|雄鹿|掘金|太阳|热火|尼克斯|森林狼|骑士|雷霆|步行者|活塞|76人|篮网|老鹰|黄蜂|公牛|猛龙|魔术|奇才|开拓者|灰熊|马刺|国王|火箭|鹈鹕|爵士|库里|詹姆斯|杜兰特|文班亚马|哈登")

BILI_HOME = "https://www.bilibili.com/"
BILI_SEARCH = "https://api.bilibili.com/x/web-interface/search/type"
ESPN_HEAT_SCHEDULE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/mia/schedule"


def _warm_bili_cookies(client: httpx.Client) -> None:
    """B 站搜索接口不带 Cookie 时直接返回 412 风控（只有几十字节的拦截页）。
    先访问一次首页拿到 buvid3，实测 412 消失、整轮抓取从 20 秒降到 2~3 秒。
    这一步失败不影响其他源，B 站板块自己会标记拉取失败。"""
    try:
        client.get(BILI_HOME, timeout=6)
    except Exception:
        pass


def _merge(fresh: dict, old) -> dict:
    """本轮某个源没抓到内容时，沿用上一次成功的内容，并记录它是几点抓的。
    避免一次网络抖动就把页面上已有的新闻清空。"""
    if not old:
        return fresh
    stale = dict(fresh.get("stale") or {})
    old_stale = old.get("stale") or {}
    for k in ("ai", "nba", "csgo"):
        if not fresh.get(k) and old.get(k):
            fresh[k] = old[k]
            stale[k] = old_stale.get(k) or old.get("updated")
    if stale:
        fresh["stale"] = stale
    return fresh


def _warm_cache():
    """启动预热：服务一起来就后台抓一次，消除重启后首次访问的长等待"""
    try:
        fresh = fetch_all()
        with _cache_lock:
            _cache["data"] = fresh
            _cache["ts"] = time.time()
    except Exception as e:
        print("warm-up failed:", repr(e), flush=True)


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=_warm_cache, daemon=True).start()
    yield


app = FastAPI(title="Still Here 情报站", description="每日要闻实时抓取接口", lifespan=lifespan)


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
    """B 站接口带退避重试（限流时返回 412 或小体积非 JSON，间隔递增重试）"""
    last_err = None
    for attempt, wait in enumerate([0, 3, 8], start=1):
        if wait:
            time.sleep(wait)
        try:
            r = client.get(BILI_SEARCH, params=params)
            # 412 = 风控拦截；体积过小说明被拦截页/空响应
            if r.status_code == 412 or len(r.content) < 3000:
                last_err = RuntimeError("rate-limited ({} / {} bytes)".format(r.status_code, len(r.content)))
                continue
            return r.json()
        except Exception as e:
            last_err = e
    raise last_err or RuntimeError("bilibili failed")


def fetch_source(client: httpx.Client, kind: str) -> tuple:
    """抓取单个源，返回 (key, items, failed)。非 B 站源失败时原地重试一次，
    覆盖偶发的 SSL 断连（实测量子位/HLTV 会间歇报 UNEXPECTED_EOF）。"""
    last_err = None
    for attempt in range(2):
        if attempt:
            time.sleep(1)
        try:
            return _fetch_source_once(client, kind)
        except Exception as e:
            last_err = e
    print("[fetch] %s 拉取失败: %r" % (kind, last_err), flush=True)
    return kind, [], True


def _fetch_source_once(client: httpx.Client, kind: str) -> tuple:
    if kind == "ai":  # 量子位 RSS，24 小时内
        r = client.get("https://www.qbitai.com/feed")
        return kind, parse_rss(r.text, 4, 24), False

    if kind == "nba":  # B 站最新战报，36 小时内且标题须 NBA 相关
        r = bili_get(client, {"search_type": "video", "order": "pubdate", "keyword": "NBA战报"})
        return kind, bili_items(r, 4, "", 36, NBA_TEAMS), False

    if kind == "csgo_hltv":  # HLTV 国际要闻，72 小时内
        r = client.get("https://www.hltv.org/rss/news")
        return kind, parse_rss(r.text, 2, 72), False

    if kind == "csgo_up":  # CSGO-DOUBLEup 最新视频，72 小时内
        r = bili_get(client, {"search_type": "video", "order": "pubdate", "keyword": "CSGO-DOUBLEup"})
        return kind, bili_items(r, 2, "CSGO", 72), False

    if kind == "heat_schedule":  # 热火队近期赛程（ESPN 官方接口，休赛日兜底）
        r = client.get(ESPN_HEAT_SCHEDULE)
        data = r.json()
        out = []
        for e in (data.get("events") or []):
            date_raw = str(e.get("date") or "")[:16].replace("T", " ")
            teams = []
            score_part = ""
            for comp in ((e.get("competitions") or [{}])[0].get("competitors") or []):
                teams.append(comp.get("team", {}).get("displayName", "?"))
                sc = comp.get("score")
                if sc:
                    score_part += (" " + str(sc.get("displayValue", ""))) if isinstance(sc, dict) else (" " + str(sc))
            if len(teams) >= 2:
                line = "{} @ {}".format(teams[1], teams[0])
                if score_part:
                    line += "（比分{}）".format(score_part.strip())
                out.append({"t": "{} · {}".format(date_raw, line), "u": "https://www.espn.com/nba/team/_/name/mia/miami-heat"})
            if len(out) >= 4:
                break
        return kind, out, False

    raise RuntimeError("unknown source: %s" % kind)


def fetch_all() -> dict:
    """并发抓取全部数据源，返回聚合结果"""
    keys = ["ai", "nba", "csgo_hltv", "csgo_up", "heat_schedule"]
    data = {}
    with httpx.Client(headers=HEADERS, timeout=12, follow_redirects=True) as client:
        _warm_bili_cookies(client)
        with ThreadPoolExecutor(max_workers=5) as pool:
            for kind, items, failed in pool.map(lambda k: fetch_source(client, k), keys):
                data[kind] = {"items": items, "failed": failed}

    csgo = data["csgo_hltv"]["items"] + data["csgo_up"]["items"]
    now = datetime.now()
    failed = [k for k in ["ai", "nba"] if data[k]["failed"] and not data[k]["items"]]
    if not csgo and (data["csgo_hltv"]["failed"] or data["csgo_up"]["failed"]):
        failed.append("csgo")

    # NBA：有战报给战报；没有则给热火近期赛程兜底，板块永远有内容
    nba_final = data["nba"]["items"] or data["heat_schedule"]["items"]
    nba_failed = bool(data["nba"]["failed"]) and bool(data["heat_schedule"]["failed"])
    if nba_failed:
        failed.append("nba")

    return {
        "date": now.strftime("%Y-%m-%d"),
        "updated": now.strftime("%H:%M"),
        "ai": data["ai"]["items"],
        "nba": nba_final,
        "nba_is_schedule": not data["nba"]["items"],
        "csgo": csgo,
        "failed": failed,
    }


@app.get("/api/news", summary="实时抓取三个板块的要闻")
def get_news(force: int = 0):
    """AI(24h) / NBA(36h) / CS:GO(72h)，各源独立容错。
    10 分钟内的调用直接返回缓存；缓存过期时立即返回旧数据并在后台刷新
    （Stale-While-Revalidate），用户永远不用对着白屏等待。
    ?force=1 时同步抓取并等待新结果返回（前端「实时刷新」按钮走这条路），
    并发的强制刷新共用同一轮抓取；某源这一轮没抓到内容时沿用上次的内容。"""
    now_ts = time.time()
    with _cache_lock:
        cached = _cache["data"]
        ts = _cache["ts"]

    def send(data: dict) -> dict:
        if not data.get("refreshing"):
            data = dict(data)
            data.pop("refreshing", None)
        return data

    if force:
        # 刚刚有别的请求抓完，直接复用，别连着打数据源
        if cached and now_ts - ts < FORCE_FRESH_WINDOW:
            return send(cached)
        with _fetch_lock:
            with _cache_lock:
                cached = _cache["data"]
                ts = _cache["ts"]
            if cached and time.time() - ts < FORCE_FRESH_WINDOW:
                return send(cached)
            fresh = _merge(fetch_all(), cached)
            with _cache_lock:
                _cache["data"] = fresh
                _cache["ts"] = time.time()
            return send(fresh)

    if cached and now_ts - ts < CACHE_TTL:
        return send(cached)

    # 有旧数据：立即返回 + 后台刷新（不打扰用户）
    if cached:
        with _refresh_lock:
            if _refreshing["v"]:
                return {**cached, "refreshing": True}
            _refreshing["v"] = True

        def bg():
            try:
                fresh = _merge(fetch_all(), _cache["data"])
                with _cache_lock:
                    _cache["data"] = fresh
                    _cache["ts"] = time.time()
            finally:
                with _refresh_lock:
                    _refreshing["v"] = False

        threading.Thread(target=bg, daemon=True).start()
        return {**cached, "refreshing": True}

    # 无任何缓存：同步抓取（首次访问，等一下值得）
    result = fetch_all()
    with _cache_lock:
        _cache["data"] = result
        _cache["ts"] = time.time()
    return result


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/test1.html", include_in_schema=False)
def old_home():
    """旧地址跳转，历史书签不失效"""
    return RedirectResponse("/", status_code=301)


# 静态文件兜底（图片、news-data.js、philosophy-data.js 等），必须最后挂载
app.mount("/", StaticFiles(directory=BASE_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="127.0.0.1", port=8898)
    except OSError:
        print("端口 8898 已被占用——服务可能已经在运行。")
        print("浏览器直接访问 http://127.0.0.1:8898/ 即可。")
        try:
            input("按回车键关闭本窗口...")
        except EOFError:
            pass
