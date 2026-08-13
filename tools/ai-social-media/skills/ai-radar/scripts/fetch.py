#!/usr/bin/env python3
"""ai-radar 自包含抓取器。

标准库优先（urllib + xml.etree 解析 RSS/Atom，HN/HF/Reddit 走 JSON API），
feedparser/httpx 可用则自动升级——裸 Python 3.8+ 即可运行，零必装依赖。

用法:
    python fetch.py                      # 默认抓近 36h，全部启用源
    python fetch.py --since 7d           # 近 7 天（周报）
    python fetch.py --since 30d          # 近 30 天（月报）
    python fetch.py --categories vendor,community
    python fetch.py --sources path/to/sources.json

输出（stdout，JSON）:
    {
      "items": [{title,url,source,category,published_at,summary_raw,extra}],
      "dynamic_sources": [{name,query}],   # 交给宿主 agent 用 WebSearch 补抓
      "failed_sources": ["name: reason"],
      "stats": {fetched, sources_ok, sources_failed, window_hours}
    }
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (compatible; ai-radar/1.0; +https://github.com/ai-radar)"
TIMEOUT = 20

try:  # 可选升级：更鲁棒的 HTTP
    import httpx  # type: ignore

    def http_get(url: str) -> str:
        r = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        return r.text
except ImportError:

    def http_get(url: str) -> str:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=TIMEOUT) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")


def http_get_json(url: str):
    return json.loads(http_get(url))


# ── RSS/Atom 解析（feedparser 可用则用，否则 xml.etree）──

try:
    import feedparser  # type: ignore

    def parse_feed(text: str) -> list:
        out = []
        for e in feedparser.parse(text).entries:
            out.append(
                {
                    "title": (e.get("title") or "").strip(),
                    "url": e.get("link") or "",
                    "published_at": _struct_to_iso(e.get("published_parsed") or e.get("updated_parsed")),
                    "summary_raw": _strip_html(e.get("summary") or (e.get("content", [{}])[0].get("value", "") if e.get("content") else "")),
                }
            )
        return [i for i in out if i["title"] and i["url"]]

except ImportError:
    import xml.etree.ElementTree as ET

    _NS = {"atom": "http://www.w3.org/2005/Atom"}

    def parse_feed(text: str) -> list:
        out = []
        try:
            root = ET.fromstring(text.encode("utf-8") if isinstance(text, str) else text)
        except ET.ParseError:
            return out
        # RSS 2.0: channel/item
        for item in root.iter("item"):
            title = _text(item.find("title"))
            link = _text(item.find("link"))
            pub = _text(item.find("pubDate"))
            desc = _text(item.find("description"))
            if title and link:
                out.append({"title": title, "url": link, "published_at": _rfc822_to_iso(pub), "summary_raw": _strip_html(desc)})
        if out:
            return out
        # Atom: entry
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            title = _text(entry.find("atom:title", _NS))
            link_el = entry.find("atom:link", _NS)
            link = link_el.get("href") if link_el is not None else ""
            pub = _text(entry.find("atom:updated", _NS)) or _text(entry.find("atom:published", _NS))
            summ = _text(entry.find("atom:summary", _NS)) or _text(entry.find("atom:content", _NS))
            if title and link:
                out.append({"title": title, "url": link, "published_at": pub or None, "summary_raw": _strip_html(summ)})
        return out

    def _text(el):
        return (el.text or "").strip() if el is not None and el.text else ""

    def _rfc822_to_iso(s: str):
        if not s:
            return None
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
            try:
                return datetime.strptime(s, fmt).astimezone(timezone.utc).isoformat()
            except ValueError:
                continue
        return None


def _struct_to_iso(t):
    if not t:
        return None
    return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc).isoformat()


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(s: str, limit: int = 2000) -> str:
    if not s:
        return ""
    return _TAG_RE.sub(" ", s).replace("&nbsp;", " ").strip()[:limit]


# ── 时间窗口 ──


def parse_since(s: str) -> float:
    """'36h' / '7d' / '30d' → 秒。"""
    m = re.match(r"^(\d+)\s*([hd])$", s.strip())
    if not m:
        return 36 * 3600
    n, unit = int(m.group(1)), m.group(2)
    return n * (3600 if unit == "h" else 86400)


def _within(iso: str | None, cutoff_ts: float) -> bool:
    if not iso:
        return True  # 无时间戳的保留（让 agent 判断）
    try:
        return datetime.fromisoformat(iso).timestamp() >= cutoff_ts
    except ValueError:
        return True


def _iso_to_ts(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


# ── 各 method 抓取 ──


def fetch_rss(src: dict, cutoff_ts: float) -> list:
    items = parse_feed(http_get(src["url"]))
    out = []
    for it in items:
        if not _within(it.get("published_at"), cutoff_ts):
            continue
        out.append({**it, "source": src["name"], "category": src["category"]})
    return out


def fetch_hackernews(src: dict, cutoff_ts: float) -> list:
    keywords = ["AI", "LLM", "GPT", "Claude", "Gemini", "agent", "open source model", "MCP", "agent skill", "Claude skill"]
    since = int(cutoff_ts)
    seen, out = set(), []
    for kw in keywords:
        url = (
            f"https://hn.algolia.com/api/v1/search_by_date?query={kw}&tags=story"
            f"&numericFilters=points%3E100,created_at_i%3E{since}&hitsPerPage=30"
        )
        try:
            data = http_get_json(url)
        except Exception:
            continue
        for hit in data.get("hits", []):
            if (hit.get("points") or 0) < 100:
                continue
            link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            if link in seen:
                continue
            seen.add(link)
            out.append(
                {
                    "title": (hit.get("title") or "").strip(),
                    "url": link,
                    "source": src["name"],
                    "category": src["category"],
                    "published_at": datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc).isoformat() if hit.get("created_at_i") else None,
                    "summary_raw": (hit.get("story_text") or "")[:1000],
                    "extra": {"points": hit.get("points"), "comments": hit.get("num_comments")},
                }
            )
    return [i for i in out if i["title"]]


def fetch_hf_papers(src: dict, cutoff_ts: float) -> list:
    out = []
    for entry in http_get_json("https://huggingface.co/api/daily_papers?limit=20"):
        paper = entry.get("paper") or {}
        pid, title = paper.get("id"), (paper.get("title") or "").strip().replace("\n", " ")
        if not pid or not title:
            continue
        out.append(
            {
                "title": title,
                "url": f"https://huggingface.co/papers/{pid}",
                "source": src["name"],
                "category": src["category"],
                "published_at": entry.get("publishedAt"),
                "summary_raw": (paper.get("summary") or "")[:2000],
                "extra": {"upvotes": paper.get("upvotes", 0)},
            }
        )
    return out


def fetch_hf_models(src: dict, cutoff_ts: float) -> list:
    url = "https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=15"
    out = []
    for m in http_get_json(url):
        mid = m.get("id") or m.get("modelId")
        if not mid:
            continue
        out.append(
            {
                "title": f"HF Trending Model: {mid}",
                "url": f"https://huggingface.co/{mid}",
                "source": src["name"],
                "category": src["category"],
                "published_at": m.get("createdAt"),
                "summary_raw": f"pipeline={m.get('pipeline_tag', '')}; downloads={m.get('downloads', 0)}; likes={m.get('likes', 0)}",
                "extra": {"likes": m.get("likes", 0), "downloads": m.get("downloads", 0)},
            }
        )
    return out


def fetch_hf_spaces(src: dict, cutoff_ts: float) -> list:
    """HF Spaces trending（热门 AI 应用 demo）。"""
    url = "https://huggingface.co/api/spaces?sort=trendingScore&direction=-1&limit=15"
    out = []
    for s in http_get_json(url):
        sid = s.get("id")
        if not sid:
            continue
        out.append(
            {
                "title": f"HF Space: {sid}",
                "url": f"https://huggingface.co/spaces/{sid}",
                "source": src["name"],
                "category": src["category"],
                "published_at": s.get("createdAt"),
                "summary_raw": f"AI 应用 demo（sdk: {s.get('sdk', '')}）; likes: {s.get('likes', 0)}",
                "extra": {"likes": s.get("likes", 0), "sdk": s.get("sdk", "")},
            }
        )
    return out


def fetch_reddit(src: dict, cutoff_ts: float) -> list:
    data = http_get_json(src["url"])
    out = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        if (d.get("score") or 0) < 50:
            continue
        title, permalink = (d.get("title") or "").strip(), d.get("permalink") or ""
        if not title or not permalink:
            continue
        out.append(
            {
                "title": title,
                "url": f"https://www.reddit.com{permalink}",
                "source": src["name"],
                "category": src["category"],
                "published_at": datetime.fromtimestamp(d["created_utc"], tz=timezone.utc).isoformat() if d.get("created_utc") else None,
                "summary_raw": (d.get("selftext") or "")[:1000],
                "extra": {"score": d.get("score")},
            }
        )
    return out


class _TrendingParser(HTMLParser):
    """极简解析 github.com/trending 的 <article class=Box-row> 仓库名。"""

    def __init__(self):
        super().__init__()
        self.repos: list[str] = []
        self._in_h2_a = False
        self._depth_h2 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h2":
            self._depth_h2 = 1
        elif tag == "a" and self._depth_h2 and a.get("href", "").count("/") == 2:
            self._in_h2_a = True
            self._href = a["href"]

    def handle_endtag(self, tag):
        if tag == "h2":
            self._depth_h2 = 0
        elif tag == "a" and self._in_h2_a:
            self._in_h2_a = False

    def handle_data(self, data):
        if self._in_h2_a and self._href:
            self.repos.append(self._href.strip("/"))
            self._href = ""


_AI_RE = re.compile(
    r"\b(ai|llms?|gpts?|claude|gemini|agents?|agentic|rag|diffusion|transformers?|models?|mcp|copilot|inference|neural|llama|prompt|embedding|vector|langchain|autogen)\b",
    re.I,
)


def _format_stars(stars: int) -> str:
    if stars >= 1000:
        return f"{stars / 1000:.1f}k".replace(".0k", "k")
    return str(stars)


def _as_list(value, default: list[str]) -> list[str]:
    if value is None:
        return default
    if isinstance(value, str):
        return [value]
    return list(value)


def _github_stars_profile(src: dict, cutoff_ts: float) -> dict:
    """根据报告时间窗切换 GitHub 项目追踪口径。

    GitHub Search API 不提供「近 N 天新增 star」字段，所以：
    - 日报：看近 7 天创建的新项目，抓早期爆发；
    - 周报：看近 30 天创建且已积累高星的项目，作为增长动量代理；
    - 月报：看高星且近期仍活跃的基础设施项目，用于生态格局判断。
    """
    now = time.time()
    report_window_days = max(1, round((now - cutoff_ts) / 86400)) if cutoff_ts > 0 else 1
    periods = src.get("periods") or {}
    default_queries = _as_list(src.get("query"), ["topic:llm", "topic:ai-agents", "topic:generative-ai"])

    if report_window_days <= 2:
        period, defaults = (
            "daily",
            {
                "label": "日报·近7天新项目",
                "strategy": "new",
                "freshness": "created",
                "lookback_days": int(src.get("lookback_days", 7)),
                "min_stars": int(src.get("min_stars", 50)),
            },
        )
    elif report_window_days <= 10:
        period, defaults = (
            "weekly",
            {
                "label": "周报·近30天动量项目",
                "strategy": "momentum",
                "freshness": "created",
                "lookback_days": int(src.get("weekly_lookback_days", 30)),
                "min_stars": int(src.get("weekly_min_stars", 100)),
            },
        )
    else:
        period, defaults = (
            "monthly",
            {
                "label": "月报·基础设施活跃项目",
                "strategy": "foundation",
                "freshness": "pushed",
                "lookback_days": int(src.get("monthly_active_days", 180)),
                "min_stars": int(src.get("monthly_min_stars", 5000)),
            },
        )

    cfg = periods.get(period, {})
    lookback_days = int(cfg.get("active_days", cfg.get("lookback_days", defaults["lookback_days"])))
    fresh_cutoff_ts = now - lookback_days * 86400
    return {
        "period": period,
        "window_days": report_window_days,
        "label": cfg.get("label", defaults["label"]),
        "strategy": cfg.get("strategy", defaults["strategy"]),
        "freshness": cfg.get("freshness", defaults["freshness"]),
        "lookback_days": lookback_days,
        "min_stars": int(cfg.get("min_stars", defaults["min_stars"])),
        "limit": int(cfg.get("limit", src.get("limit", 12))),
        "query": _as_list(cfg.get("query"), default_queries),
        "fresh_cutoff_ts": fresh_cutoff_ts,
    }


def fetch_github_trending(src: dict, cutoff_ts: float) -> list:
    p = _TrendingParser()
    p.feed(http_get(src["url"]))
    out = []
    for repo in p.repos:
        if not _AI_RE.search(repo):
            continue
        out.append(
            {
                "title": repo,
                "url": f"https://github.com/{repo}",
                "source": src["name"],
                "category": src["category"],
                "published_at": None,
                "summary_raw": "",
            }
        )
    return out


def fetch_github_stars(src: dict, cutoff_ts: float) -> list:
    """GitHub Search API：按日报/周报/月报切换 GitHub 项目追踪口径。

    GitHub repository search 不支持 qualifier（topic:/stars:/pushed:）之间的 OR，
    也不暴露「近 N 天新增 stars」排序，故用时间窗代理：日报/周报约束
    created:>N 天，月报约束 pushed:>N 天，把多个 topic/关键词逐个查询后
    合并去重，再按当前 stars 排序取 top。
    """
    profile = _github_stars_profile(src, cutoff_ts)
    since_date = time.strftime("%Y-%m-%d", time.gmtime(profile["fresh_cutoff_ts"]))
    freshness = "pushed" if profile["freshness"] == "pushed" else "created"
    timestamp_key = f"{freshness}_at"
    seen, out = set(), []
    for query in profile["query"]:
        q = f"{query} stars:>{profile['min_stars']} {freshness}:>{since_date}".replace(" ", "+")
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={profile['limit']}"
        try:
            items = http_get_json(url).get("items", [])
        except (URLError, Exception):  # noqa: B014 — 单 query 失败不拖累其余 topic
            continue
        for r in items:
            name = r.get("full_name", "")
            if not name or name in seen:
                continue
            description = r.get("description") or ""
            topics = " ".join(r.get("topics") or [])
            if not _AI_RE.search(f"{name} {description} {topics}"):
                continue
            fresh_ts = _iso_to_ts(r.get(timestamp_key))
            if fresh_ts and fresh_ts < profile["fresh_cutoff_ts"]:
                continue
            seen.add(name)
            stars = r.get("stargazers_count", 0)
            lang = r.get("language") or ""
            created_at = r.get("created_at")
            pushed_at = r.get("pushed_at")
            published_at = created_at if freshness == "created" else (pushed_at or r.get("updated_at") or created_at)
            out.append(
                {
                    "title": f"{name} (⭐{_format_stars(stars)}{' ' + lang if lang else ''})",
                    "url": r.get("html_url", ""),
                    "source": src["name"],
                    "category": src["category"],
                    "published_at": published_at,
                    "summary_raw": f"{profile['label']}; stars={stars}; {description[:180]}",
                    "extra": {
                        "stars": stars,
                        "language": lang,
                        "created_at": created_at,
                        "pushed_at": pushed_at,
                        "lookback_days": profile["lookback_days"],
                        "min_stars": profile["min_stars"],
                        "github_period": profile["period"],
                        "github_strategy": profile["strategy"],
                        "freshness": freshness,
                    },
                }
            )
    out.sort(key=lambda x: -x["extra"]["stars"])
    return out[: profile["limit"]]


FETCHERS = {
    "rss": fetch_rss,
    "hackernews": fetch_hackernews,
    "hf_papers": fetch_hf_papers,
    "hf_models": fetch_hf_models,
    "hf_spaces": fetch_hf_spaces,
    "reddit": fetch_reddit,
    "github_trending": fetch_github_trending,
    "github_stars": fetch_github_stars,
}


def run(sources: list, since_seconds: float, categories: set | None) -> dict:
    cutoff_ts = time.time() - since_seconds
    items, dynamic, failed, ok = [], [], [], 0
    for src in sources:
        if not src.get("enabled", True):
            continue
        if categories and src.get("category") not in categories:
            continue
        if src.get("method") == "dynamic":
            dynamic.append({"name": src["name"], "query": src.get("query", src["name"])})
            continue
        fetcher = FETCHERS.get(src.get("method"))
        if not fetcher:
            failed.append(f"{src['name']}: unknown method {src.get('method')}")
            continue
        try:
            got = fetcher(src, cutoff_ts)
            items.extend(got)
            ok += 1
        except (URLError, Exception) as e:  # noqa: B014 — 单源隔离
            failed.append(f"{src['name']}: {type(e).__name__}: {str(e)[:120]}")
    return {
        "items": items,
        "dynamic_sources": dynamic,
        "failed_sources": failed,
        "stats": {
            "fetched": len(items),
            "sources_ok": ok,
            "sources_failed": len(failed),
            "window_hours": round(since_seconds / 3600, 1),
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ai-radar 自包含抓取器")
    ap.add_argument("--since", default="36h", help="时间窗口：36h / 7d / 30d")
    ap.add_argument("--categories", default="", help="逗号分隔的来源大类过滤（留空=全部）")
    ap.add_argument("--sources", default=str(Path(__file__).parent / "sources.json"))
    args = ap.parse_args(argv)

    spec = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    sources = spec.get("sources", spec) if isinstance(spec, dict) else spec
    cats = {c.strip() for c in args.categories.split(",") if c.strip()} or None

    result = run(sources, parse_since(args.since), cats)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
